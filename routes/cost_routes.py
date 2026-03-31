from __future__ import annotations

from datetime import datetime
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Header, HTTPException, Request

from app.analytics import analytics_store
from app.cost import cost_service

router = APIRouter()

_ANALYTICS_API_KEY = os.environ.get("VERIFAI_ANALYTICS_API_KEY")


def _check_api_key(request: Request, x_api_key: Optional[str]) -> None:
    if not _ANALYTICS_API_KEY:
        return
    candidate = x_api_key or request.query_params.get("api_key")
    if candidate != _ANALYTICS_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid analytics API key")


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


def _build_recent_activity(records: list, limit: int = 6) -> List[Dict[str, Any]]:
    activities = []
    sorted_records = sorted(records, key=lambda r: r.timestamp, reverse=True)
    for record in sorted_records:
        if record.cost_usd <= 0:
            continue
        activities.append(
            {
                "timestamp": record.timestamp,
                "type": record.event_type,
                "cost": record.cost_usd,
                "model": record.model,
            }
        )
        if len(activities) >= limit:
            break
    return activities


@router.get("/cost/dashboard")
async def cost_dashboard(
    request: Request,
    days: int = 30,
    x_api_key: Optional[str] = Header(None),
) -> Dict[str, Any]:
    _check_api_key(request, x_api_key)
    now = datetime.utcnow().isoformat()
    summary = analytics_store.get_summary_for_days(days)
    total_cost = summary.total_cost
    total_reviews = summary.total_episodes
    average_cost = total_cost / total_reviews if total_reviews else 0.0

    return {
        "summary": {
            "totalCost": total_cost,
            "totalReviews": total_reviews,
            "averageCost": round(average_cost, 4),
            "costSaved": summary.cost_saved,
        },
        "breakdown": _build_cost_breakdown(summary),
        "budget": cost_service.get_budget_status(total_cost),
        "recentActivity": _build_recent_activity(analytics_store.get_records(days)),
        "lastUpdated": now,
    }


@router.get("/cost/optimizations")
async def cost_optimizations(
    request: Request,
    days: int = 30,
    x_api_key: Optional[str] = Header(None),
) -> Dict[str, Any]:
    _check_api_key(request, x_api_key)
    summary = analytics_store.get_summary_for_days(days)
    suggestions = cost_service.list_optimizations(summary)
    return {"suggestions": suggestions}


@router.post("/cost/optimizations/{suggestion_id}/apply")
async def apply_optimization(
    request: Request,
    suggestion_id: str,
    x_api_key: Optional[str] = Header(None),
) -> Dict[str, Any]:
    _check_api_key(request, x_api_key)
    cost_service.apply_optimization(suggestion_id)
    return {"applied": True, "suggestion_id": suggestion_id}


@router.post("/cost/budget")
async def set_budget(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    x_api_key: Optional[str] = Header(None),
) -> Dict[str, Any]:
    _check_api_key(request, x_api_key)
    config = cost_service.set_budget(payload)
    summary = analytics_store.get_summary()
    return {
        "budget": cost_service.get_budget_status(summary.total_cost),
        "config": {
            "daily_budget": config.daily_budget,
            "weekly_budget": config.weekly_budget,
            "monthly_budget": config.monthly_budget,
            "alert_threshold": config.alert_threshold,
            "critical_threshold": config.critical_threshold,
        },
    }
