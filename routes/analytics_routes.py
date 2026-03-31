# ANALYTICS
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta
import json
import os
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.responses import HTMLResponse

from app.analytics import analytics_store
from app.dashboard import get_dashboard_html

router = APIRouter()

_ANALYTICS_API_KEY = os.environ.get("VERIFAI_ANALYTICS_API_KEY")


def _check_api_key(request: Request, x_api_key: Optional[str]) -> None:
    if not _ANALYTICS_API_KEY:
        return
    candidate = x_api_key or request.query_params.get("api_key")
    if candidate != _ANALYTICS_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid analytics API key")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, x_api_key: Optional[str] = Header(None)) -> HTMLResponse:
    _check_api_key(request, x_api_key)
    return HTMLResponse(content=get_dashboard_html())


@router.get("/analytics/summary")
async def analytics_summary(request: Request, x_api_key: Optional[str] = Header(None)) -> dict:
    _check_api_key(request, x_api_key)
    summary = analytics_store.get_summary()
    return asdict(summary)


def _percent_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return round(((current - previous) / previous) * 100, 2)


def _roi_percent(total_cost: float, cost_saved: float) -> float:
    if total_cost <= 0:
        return 0.0
    return round((cost_saved / total_cost) * 100, 2)


def _build_quality_series(records: list, days: int) -> List[Dict[str, Any]]:
    today = datetime.utcnow().date()
    daily_scores: Dict[str, list[float]] = {}

    for record in records:
        if getattr(record, "event_type", "review") not in {"review", "multi_agent"}:
            continue
        try:
            timestamp = datetime.fromisoformat(record.timestamp)
        except ValueError:
            continue
        day_key = timestamp.date().isoformat()
        daily_scores.setdefault(day_key, []).append(record.score)

    series = []
    rolling: list[float] = []

    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        key = day.isoformat()
        scores = daily_scores.get(key, [])
        avg_score = sum(scores) / len(scores) if scores else 0.0
        rolling.append(avg_score)
        window = rolling[-7:]
        moving = sum(window) / len(window) if window else 0.0
        series.append(
            {
                "date": key,
                "score": round(avg_score, 4),
                "movingAverage": round(moving, 4),
            }
        )

    return series


def _build_cost_breakdown(summary) -> Dict[str, Any]:
    total = summary.total_cost
    by_task = []
    for task_id, entry in summary.by_task.items():
        value = entry.get("total_cost", 0.0)
        by_task.append(
            {
                "name": task_id,
                "value": value,
                "percentage": round((value / total) * 100, 2) if total else 0.0,
            }
        )

    by_model = [
        {
            "name": model,
            "value": value,
            "percentage": round((value / total) * 100, 2) if total else 0.0,
        }
        for model, value in summary.by_model.items()
    ]

    by_agent = [
        {
            "name": agent,
            "value": value,
            "percentage": round((value / total) * 100, 2) if total else 0.0,
        }
        for agent, value in summary.by_agent.items()
    ]

    return {
        "byModel": by_model,
        "byAgent": by_agent,
        "byTask": by_task,
    }


def _build_savings(cost_saved: float) -> List[Dict[str, Any]]:
    if cost_saved <= 0:
        return []
    labor = round(cost_saved * 0.4, 2)
    error = round(cost_saved * 0.35, 2)
    brand = round(cost_saved - labor - error, 2)
    return [
        {"name": "Labor", "value": labor, "percentage": 40},
        {"name": "Error", "value": error, "percentage": 35},
        {"name": "Brand", "value": brand, "percentage": 25},
    ]


def _build_activity(records: list, limit: int = 6) -> List[Dict[str, Any]]:
    activities = []
    sorted_records = sorted(records, key=lambda r: r.timestamp, reverse=True)
    for record in sorted_records[:limit]:
        activities.append(
            {
                "timestamp": record.timestamp,
                "type": record.event_type,
                "score": record.score,
                "cost": record.cost_usd,
            }
        )
    return activities


def _build_alerts(summary) -> List[Dict[str, Any]]:
    alerts = []
    if summary.avg_score and summary.avg_score < 0.7:
        alerts.append(
            {
                "level": "warning",
                "title": "Quality dip",
                "message": "Average score fell below 0.7. Investigate recent outputs.",
            }
        )
    if summary.total_cost > 1000:
        alerts.append(
            {
                "level": "critical",
                "title": "High spend",
                "message": "Total cost exceeded $1,000 for this period.",
            }
        )
    if summary.total_episodes == 0:
        alerts.append(
            {
                "level": "info",
                "title": "No activity",
                "message": "No reviews recorded yet. Run a task to populate analytics.",
            }
        )
    return alerts


def _build_dashboard_payload(days: int) -> Dict[str, Any]:
    now = datetime.utcnow()
    current_start = now - timedelta(days=days)
    previous_start = current_start - timedelta(days=days)

    current_summary = analytics_store.get_summary_between(current_start, now)
    previous_summary = analytics_store.get_summary_between(previous_start, current_start)

    current_roi = _roi_percent(current_summary.total_cost, current_summary.cost_saved)
    previous_roi = _roi_percent(previous_summary.total_cost, previous_summary.cost_saved)

    trends = {
        "reviews": _percent_change(current_summary.total_episodes, previous_summary.total_episodes),
        "score": _percent_change(current_summary.avg_score, previous_summary.avg_score),
        "cost": _percent_change(current_summary.total_cost, previous_summary.total_cost),
        "roi": _percent_change(current_roi, previous_roi),
    }

    records = analytics_store.get_records(days)
    review_records = analytics_store.get_review_records(days)
    quality_data = _build_quality_series(review_records, days)

    return {
        "summary": {
            "totalReviews": current_summary.total_episodes,
            "averageScore": current_summary.avg_score,
            "totalCost": current_summary.total_cost,
            "roi": current_roi,
            "trends": trends,
        },
        "qualityData": quality_data,
        "costData": _build_cost_breakdown(current_summary),
        "savingsData": _build_savings(current_summary.cost_saved),
        "recentActivity": _build_activity(records),
        "alerts": _build_alerts(current_summary),
        "lastUpdated": now.isoformat(),
    }


@router.get("/analytics/dashboard")
async def analytics_dashboard(
    request: Request,
    days: int = 30,
    x_api_key: Optional[str] = Header(None),
) -> Dict[str, Any]:
    _check_api_key(request, x_api_key)
    return _build_dashboard_payload(days)


@router.get("/analytics/stream")
async def analytics_stream(
    request: Request,
    days: int = 30,
    interval: int = 5,
    x_api_key: Optional[str] = Header(None),
) -> StreamingResponse:
    _check_api_key(request, x_api_key)
    def event_stream():
        while True:
            now = datetime.utcnow().isoformat()
            yield f"event: ping\ndata: {now}\n\n"

            payload = _build_dashboard_payload(days)
            data = json.dumps(payload)
            yield f"data: {data}\n\n"
            time.sleep(max(1, interval))

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/analytics/quality")
async def analytics_quality(
    request: Request,
    days: int = 30,
    x_api_key: Optional[str] = Header(None),
) -> Dict[str, Any]:
    _check_api_key(request, x_api_key)
    records = analytics_store.get_review_records(days)
    return {"data": _build_quality_series(records, days)}


@router.get("/analytics/cost")
async def analytics_cost(
    request: Request,
    days: int = 30,
    x_api_key: Optional[str] = Header(None),
) -> Dict[str, Any]:
    _check_api_key(request, x_api_key)
    summary = analytics_store.get_summary_for_days(days)
    return _build_cost_breakdown(summary)


@router.post("/analytics/roi")
async def analytics_roi(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    x_api_key: Optional[str] = Header(None),
) -> Dict[str, Any]:
    _check_api_key(request, x_api_key)
    daily_volume = max(0, int(payload.get("daily_volume", 0)))
    cost_per_review = max(0.0, float(payload.get("cost_per_review", 0)))

    baseline_annual = daily_volume * cost_per_review * 365
    verifai_cost = baseline_annual * 0.4
    annual_savings = max(0.0, baseline_annual - verifai_cost)

    labor_savings = annual_savings * 0.4
    error_savings = annual_savings * 0.2
    brand_savings = annual_savings * 0.15
    compliance_savings = annual_savings * 0.15
    productivity_savings = annual_savings * 0.1

    roi_percentage = (annual_savings / verifai_cost) * 100 if verifai_cost else 0.0
    payback_days = int(365 * (verifai_cost / annual_savings)) if annual_savings else 0

    return {
        "inputs": {
            "daily_volume": daily_volume,
            "cost_per_review": cost_per_review,
        },
        "annual_savings": annual_savings,
        "labor_savings": labor_savings,
        "error_savings": error_savings,
        "brand_savings": brand_savings,
        "compliance_savings": compliance_savings,
        "productivity_savings": productivity_savings,
        "verifai_cost": verifai_cost,
        "net_profit": annual_savings,
        "roi_percentage": roi_percentage,
        "payback_days": payback_days,
        "five_year_savings": annual_savings * 5,
        "recommendations": [
            "Prioritize high-volume workflows for early ROI.",
            "Track quality metrics alongside cost savings.",
        ],
    }


@router.get("/analytics/benchmarks/{industry}")
async def analytics_benchmarks(
    request: Request,
    industry: str,
    x_api_key: Optional[str] = Header(None),
) -> Dict[str, Any]:
    _check_api_key(request, x_api_key)
    return {
        "industry": industry,
        "benchmarks": {
            "average_score": 0.82,
            "cost_per_review": 0.04,
            "roi_percentage": 120,
        },
    }
