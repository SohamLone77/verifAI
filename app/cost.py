from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional
import json
import os
import threading


@dataclass
class BudgetConfig:
    daily_budget: Optional[float] = None
    weekly_budget: Optional[float] = None
    monthly_budget: Optional[float] = None
    alert_threshold: float = 0.8
    critical_threshold: float = 0.95


class CostService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._budget_path = Path(os.environ.get("VERIFAI_BUDGET_PATH", "data/cost_budget.json"))
        self._budget_path.parent.mkdir(parents=True, exist_ok=True)
        self._config = BudgetConfig()
        self._applied: set[str] = set()
        self._load()

    def _load(self) -> None:
        if not self._budget_path.exists():
            return
        try:
            raw = json.loads(self._budget_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return

        if isinstance(raw, dict):
            self._config.daily_budget = self._coerce_float(raw.get("daily_budget"))
            self._config.weekly_budget = self._coerce_float(raw.get("weekly_budget"))
            self._config.monthly_budget = self._coerce_float(raw.get("monthly_budget"))
            self._config.alert_threshold = float(raw.get("alert_threshold", 0.8))
            self._config.critical_threshold = float(raw.get("critical_threshold", 0.95))

    def _persist(self) -> None:
        payload = asdict(self._config)
        self._budget_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _coerce_float(value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def get_budget_config(self) -> BudgetConfig:
        with self._lock:
            return BudgetConfig(**asdict(self._config))

    def set_budget(self, payload: dict[str, Any]) -> BudgetConfig:
        with self._lock:
            if "daily_budget" in payload:
                self._config.daily_budget = self._coerce_float(payload.get("daily_budget"))
            if "weekly_budget" in payload:
                self._config.weekly_budget = self._coerce_float(payload.get("weekly_budget"))
            if "monthly_budget" in payload:
                self._config.monthly_budget = self._coerce_float(payload.get("monthly_budget"))
            if "alert_threshold" in payload and payload.get("alert_threshold") is not None:
                self._config.alert_threshold = float(payload.get("alert_threshold"))
            if "critical_threshold" in payload and payload.get("critical_threshold") is not None:
                self._config.critical_threshold = float(payload.get("critical_threshold"))

            self._persist()
            return BudgetConfig(**asdict(self._config))

    def get_budget_status(self, total_cost: float) -> dict[str, Any]:
        with self._lock:
            config = BudgetConfig(**asdict(self._config))

        budget_limit = (
            config.monthly_budget
            if config.monthly_budget is not None
            else config.weekly_budget
            if config.weekly_budget is not None
            else config.daily_budget
            if config.daily_budget is not None
            else 0.0
        )

        if budget_limit > 0:
            usage = total_cost / budget_limit
            status = "ok"
            if usage >= config.critical_threshold:
                status = "critical"
            elif usage >= config.alert_threshold:
                status = "warning"
        else:
            usage = 0.0
            status = "unset"

        remaining = max(0.0, budget_limit - total_cost) if budget_limit else 0.0

        return {
            "budget_limit": round(budget_limit, 4) if budget_limit else 0.0,
            "current_cost": round(total_cost, 4),
            "remaining": round(remaining, 4),
            "usage_percentage": round(usage, 4),
            "status": status,
            "alert_count": 0,
            "daily_budget": config.daily_budget,
            "weekly_budget": config.weekly_budget,
            "monthly_budget": config.monthly_budget,
        }

    def list_optimizations(self, summary: Any) -> list[dict[str, Any]]:
        suggestions: list[dict[str, Any]] = []
        total_cost = getattr(summary, "total_cost", 0.0) or 0.0
        total_reviews = getattr(summary, "total_episodes", 0) or 0

        if total_cost <= 0:
            return suggestions

        by_model = getattr(summary, "by_model", {}) or {}
        if by_model:
            top_model = max(by_model, key=by_model.get)
            top_cost = by_model[top_model]
            if total_cost > 0 and top_cost >= total_cost * 0.5:
                suggestions.append(
                    {
                        "suggestion_id": "model_tiering",
                        "title": "Reduce dependency on premium models",
                        "description": (
                            f"{top_model} accounts for {round((top_cost / total_cost) * 100, 1)}% of spend. "
                            "Shift low-risk tasks to a cheaper model tier."
                        ),
                        "estimated_savings": round(top_cost * 0.35, 4),
                        "priority": "high",
                    }
                )

        if total_reviews >= 20:
            suggestions.append(
                {
                    "suggestion_id": "cache_outputs",
                    "title": "Enable response caching",
                    "description": "Cache repeated review payloads to reduce duplicate token usage.",
                    "estimated_savings": round(total_cost * 0.12, 4),
                    "priority": "medium",
                }
            )

        if self.get_budget_status(total_cost).get("status") == "unset":
            suggestions.append(
                {
                    "suggestion_id": "set_budget",
                    "title": "Set a monthly budget",
                    "description": "Define a budget to monitor usage and catch spikes early.",
                    "estimated_savings": 0.0,
                    "priority": "low",
                }
            )

        for suggestion in suggestions:
            suggestion["applied"] = suggestion["suggestion_id"] in self._applied

        return suggestions

    def apply_optimization(self, suggestion_id: str) -> None:
        with self._lock:
            self._applied.add(suggestion_id)


cost_service = CostService()
