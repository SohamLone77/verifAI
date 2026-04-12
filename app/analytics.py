# ANALYTICS
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
import json
import os
import threading


HUMAN_REVIEW_COST_USD = 0.15
_SCORE_EPSILON = 1e-6


def _normalize_open_interval_score(value: float) -> float:
    return max(_SCORE_EPSILON, min(1.0 - _SCORE_EPSILON, float(value)))


@dataclass
class EpisodeRecord:
    session_id: str
    task_id: str
    score: float
    cost_usd: float
    steps: int
    timestamp: str
    event_type: str = "review"
    model: Optional[str] = None
    model_usage: Optional[dict[str, dict[str, float]]] = None
    agent_roles: Optional[list[str]] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyticsSummary:
    total_episodes: int
    avg_score: float
    total_cost: float
    cost_saved: float
    by_task: dict[str, dict[str, Any]]
    by_model: dict[str, float] = field(default_factory=dict)
    by_agent: dict[str, float] = field(default_factory=dict)
    total_events: int = 0


class AnalyticsStore:
    def __init__(self) -> None:
        self._records: list[EpisodeRecord] = []
        self._lock = threading.Lock()
        self._store_path = Path(
            os.environ.get("VERIFAI_ANALYTICS_PATH", "data/analytics_store.json")
        )
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_from_disk()

    def append_episode(self, record: EpisodeRecord) -> None:
        with self._lock:
            record.score = _normalize_open_interval_score(record.score)
            self._records.append(record)
            self._persist()

    def clear(self) -> None:
        with self._lock:
            self._records.clear()
            self._persist()

    def _persist(self) -> None:
        payload = [asdict(record) for record in self._records]
        self._store_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _record_from_dict(self, data: dict[str, Any]) -> EpisodeRecord:
        return EpisodeRecord(
            session_id=data.get("session_id", "unknown"),
            task_id=data.get("task_id", "unknown"),
            score=_normalize_open_interval_score(float(data.get("score", 0.0))),
            cost_usd=float(data.get("cost_usd", 0.0)),
            steps=int(data.get("steps", 0)),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            event_type=data.get("event_type", "review"),
            model=data.get("model"),
            model_usage=data.get("model_usage"),
            agent_roles=data.get("agent_roles"),
            metadata=data.get("metadata", {}) or {},
        )

    def _load_from_disk(self) -> None:
        if not self._store_path.exists():
            return
        try:
            raw = json.loads(self._store_path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                self._records = [self._record_from_dict(item) for item in raw]
        except (json.JSONDecodeError, OSError):
            self._records = []

    def _parse_timestamp(self, timestamp: str) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(timestamp)
        except ValueError:
            return None

    def _filter_records(self, days: Optional[int] = None) -> list[EpisodeRecord]:
        with self._lock:
            records = list(self._records)

        if not days or days <= 0:
            return records

        cutoff = datetime.utcnow() - timedelta(days=days)
        filtered: list[EpisodeRecord] = []

        for record in records:
            parsed = self._parse_timestamp(record.timestamp)
            if parsed is None:
                filtered.append(record)
                continue

            if parsed >= cutoff:
                filtered.append(record)

        return filtered

    def _build_summary(self, records: list[EpisodeRecord]) -> AnalyticsSummary:
        review_records = [
            record
            for record in records
            if record.event_type in {"review", "multi_agent"}
        ]

        total = len(review_records)
        total_cost = round(sum(r.cost_usd for r in review_records), 4)
        avg_score = round((sum(r.score for r in review_records) / total), 4) if total else 0.0
        cost_saved = round((total * HUMAN_REVIEW_COST_USD) - total_cost, 4)

        by_task: dict[str, dict[str, Any]] = {}
        for record in review_records:
            entry = by_task.setdefault(
                record.task_id,
                {
                    "count": 0,
                    "avg_score": 0.0,
                    "total_cost": 0.0,
                    "avg_steps": 0.0,
                    "scores": [],
                    "steps": [],
                },
            )
            entry["count"] += 1
            entry["total_cost"] += record.cost_usd
            entry["scores"].append(record.score)
            entry["steps"].append(record.steps)

        for task_id, entry in by_task.items():
            count = entry["count"]
            entry["avg_score"] = round(sum(entry["scores"]) / count, 4) if count else 0.0
            entry["avg_steps"] = round(sum(entry["steps"]) / count, 4) if count else 0.0
            entry["total_cost"] = round(entry["total_cost"], 4)
            entry["task_id"] = task_id

        by_model: dict[str, float] = {}
        by_agent: dict[str, float] = {}
        for record in review_records:
            if record.model_usage:
                for model, usage in record.model_usage.items():
                    by_model[model] = by_model.get(model, 0.0) + float(usage.get("cost", 0.0))
            elif record.model:
                by_model[record.model] = by_model.get(record.model, 0.0) + record.cost_usd

            if record.agent_roles:
                split_cost = record.cost_usd / len(record.agent_roles) if record.agent_roles else 0.0
                for role in record.agent_roles:
                    by_agent[role] = by_agent.get(role, 0.0) + split_cost

        return AnalyticsSummary(
            total_episodes=total,
            avg_score=avg_score,
            total_cost=total_cost,
            cost_saved=cost_saved,
            by_task=by_task,
            by_model=by_model,
            by_agent=by_agent,
            total_events=len(records),
        )

    def get_summary(self) -> AnalyticsSummary:
        records = self._filter_records()
        return self._build_summary(records)

    def get_summary_for_days(self, days: int) -> AnalyticsSummary:
        records = self._filter_records(days)
        return self._build_summary(records)

    def get_records(self, days: Optional[int] = None) -> list[EpisodeRecord]:
        return self._filter_records(days)

    def get_review_records(self, days: Optional[int] = None) -> list[EpisodeRecord]:
        records = self._filter_records(days)
        return [
            record
            for record in records
            if record.event_type in {"review", "multi_agent"}
        ]

    def get_records_between(self, start: datetime, end: datetime) -> list[EpisodeRecord]:
        with self._lock:
            records = list(self._records)

        filtered: list[EpisodeRecord] = []
        for record in records:
            parsed = self._parse_timestamp(record.timestamp)
            if parsed is None:
                continue
            if start <= parsed < end:
                filtered.append(record)
        return filtered

    def get_summary_between(self, start: datetime, end: datetime) -> AnalyticsSummary:
        records = self.get_records_between(start, end)
        return self._build_summary(records)


analytics_store = AnalyticsStore()
