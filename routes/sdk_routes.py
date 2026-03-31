from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

import logging

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from dataclasses import asdict

from app.analytics import EpisodeRecord, analytics_store
from app.models import Rubric
from app.session import session_store
from graders.rubric_grader import RubricGrader
from verifai.agents.compliance_agent import ComplianceAgent
from verifai.agents.multi_agent_panel import MultiAgentPanel
from verifai.models.agent_models import AgentRole, ConsensusConfig, ReviewRequest as PanelReviewRequest

router = APIRouter()
_grader = RubricGrader()
logger = logging.getLogger(__name__)


class ReviewRequest(BaseModel):
    content: str
    rubric: Optional[List[str]] = None
    compliance: Optional[str] = None
    multi_agent: bool = False
    agents: Optional[List[str]] = None
    depth: Literal["quick", "standard", "deep"] = "standard"
    include_reasoning: bool = False
    max_tokens: Optional[int] = None
    temperature: float = 0.0


class SuggestRequest(BaseModel):
    content: str
    flags: List[Dict[str, Any]] = Field(default_factory=list)


class ApplyRequest(BaseModel):
    content: str
    suggestions: List[str] = Field(default_factory=list)


class ComplianceRequest(BaseModel):
    content: str
    framework: str


class MultiAgentRequest(BaseModel):
    content: str
    agents: Optional[List[str]] = None
    depth: Literal["quick", "standard", "deep"] = "standard"


class ROIRequest(BaseModel):
    daily_volume: int
    cost_per_review: float


def _build_rubric(rubric: Optional[List[str]], max_tokens: Optional[int]) -> Optional[Rubric]:
    if rubric is None and max_tokens is None:
        return None

    rubric_model = Rubric()

    if rubric:
        rubric_set = {name.strip().lower() for name in rubric if name}
        rubric_model.safety = "safety" in rubric_set
        rubric_model.brevity = "brevity" in rubric_set
        rubric_model.factuality = "factuality" in rubric_set
        rubric_model.semantic = "semantic" in rubric_set

    if max_tokens:
        rubric_model.token_budget = max_tokens

    return rubric_model


def _map_agent_roles(agent_names: Optional[List[str]]) -> Optional[List[AgentRole]]:
    if not agent_names:
        return None

    mapping = {
        "safety": AgentRole.SAFETY,
        "safety_expert": AgentRole.SAFETY,
        "factuality": AgentRole.FACTUALITY,
        "factuality_checker": AgentRole.FACTUALITY,
        "brand": AgentRole.BRAND,
        "brand_guardian": AgentRole.BRAND,
        "latency": AgentRole.LATENCY,
        "latency_analyst": AgentRole.LATENCY,
        "compliance": AgentRole.COMPLIANCE,
        "compliance_specialist": AgentRole.COMPLIANCE,
        "ux": AgentRole.UX,
        "ux_reviewer": AgentRole.UX,
    }

    roles: List[AgentRole] = []
    for name in agent_names:
        key = name.strip().lower()
        role = mapping.get(key)
        if role:
            roles.append(role)

    return roles or None


def _convert_flags(notes: List[str]) -> List[Dict[str, Any]]:
    flags: List[Dict[str, Any]] = []
    for note in notes:
        flags.append(
            {
                "type": "quality",
                "severity": 0.3,
                "description": note,
                "confidence": 0.7,
            }
        )
    return flags


def _framework_flags(content: str, framework: Optional[str]) -> List[Dict[str, Any]]:
    if not framework:
        return []

    text = content.lower()
    key = framework.lower()

    rules: Dict[str, List[Dict[str, Any]]] = {
        "gdpr": [
            {
                "type": "gdpr_data_collection",
                "terms": ["personal data", "email", "ip address", "cookie", "tracking"],
                "severity": 0.5,
                "suggestion": "Ensure lawful basis and consent for personal data processing.",
            }
        ],
        "hipaa": [
            {
                "type": "hipaa_phi",
                "terms": ["patient", "diagnosis", "medical record", "health", "phi"],
                "severity": 0.6,
                "suggestion": "Avoid exposing protected health information without safeguards.",
            }
        ],
        "pci": [
            {
                "type": "pci_card_data",
                "terms": ["credit card", "card number", "cvv", "cardholder"],
                "severity": 0.7,
                "suggestion": "Do not store or display cardholder data unless PCI controls are in place.",
            }
        ],
        "soc2": [
            {
                "type": "soc2_controls",
                "terms": ["access control", "audit log", "encryption", "availability"],
                "severity": 0.4,
                "suggestion": "Document control coverage for SOC2 trust principles.",
            }
        ],
        "ccpa": [
            {
                "type": "ccpa_personal_info",
                "terms": ["personal information", "sell", "opt out", "do not sell"],
                "severity": 0.5,
                "suggestion": "Provide opt-out and disclosure requirements for CCPA.",
            }
        ],
        "fda": [
            {
                "type": "fda_claims",
                "terms": ["treats", "cures", "medical device", "fda approved"],
                "severity": 0.7,
                "suggestion": "Avoid unapproved medical claims without FDA clearance.",
            }
        ],
    }

    flags: List[Dict[str, Any]] = []
    for rule in rules.get(key, []):
        if any(term in text for term in rule["terms"]):
            flags.append(
                {
                    "type": rule["type"],
                    "severity": rule["severity"],
                    "description": f"Potential {key.upper()} risk detected.",
                    "suggestion": rule["suggestion"],
                }
            )

    return flags


def _run_compliance(content: str, framework: Optional[str] = None) -> Dict[str, Any]:
    agent = ComplianceAgent()
    vote = agent.analyze(content)

    violations = []
    for flag in vote.flags:
        description = flag.get("claim") or flag.get("description") or "Compliance risk detected"
        violations.append(
            {
                "type": flag.get("type", "compliance_risk"),
                "severity": flag.get("severity", 0.7),
                "description": f"{description}",
                "confidence": vote.confidence,
                "suggestion": flag.get("suggestion"),
            }
        )

    framework_violations = _framework_flags(content, framework)
    violations.extend(framework_violations)

    remediation = list(vote.suggestions)
    for flag in framework_violations:
        if flag.get("suggestion"):
            remediation.append(flag["suggestion"])

    penalty = min(0.4, sum(flag.get("severity", 0.0) for flag in framework_violations) * 0.2)
    score = max(0.0, vote.score - penalty)

    if score >= 0.85:
        risk_level = "low"
    elif score >= 0.65:
        risk_level = "medium"
    elif score >= 0.4:
        risk_level = "high"
    else:
        risk_level = "critical"

    payload = {
        "score": score,
        "violations": violations,
        "remediation": remediation,
        "risk_level": risk_level,
        "confidence": vote.confidence,
    }

    if framework:
        payload["framework"] = framework

    return payload


@router.post("/review")
async def review(request: ReviewRequest) -> Dict[str, Any]:
    if not request.content or not request.content.strip():
        raise HTTPException(status_code=422, detail="Content cannot be empty.")

    rubric = _build_rubric(request.rubric, request.max_tokens)
    # Use the fast rubric grader for SDK calls to avoid heavyweight embedding loads.
    result = _grader.grade(prompt=request.content, output=request.content, rubric=rubric)

    rubric_scores = result.breakdown or {}
    if request.rubric:
        rubric_filter = {name.strip().lower() for name in request.rubric if name}
        rubric_scores = {
            key: value
            for key, value in rubric_scores.items()
            if any(dim in key.lower() for dim in rubric_filter)
        }

    response: Dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "score": result.score,
        "flags": _convert_flags(result.notes),
        "rubric_scores": rubric_scores,
        "cost": 0.0,
        "latency_ms": 0.0,
        "tokens_used": len(request.content.split()) * 3,
        "model_used": "verifai-rubric-v1",
        "reasoning_chain": result.notes if request.include_reasoning else None,
        "metadata": {},
    }

    if request.compliance:
        response["compliance_results"] = _run_compliance(request.content, request.compliance)

    if request.multi_agent:
        required_agents = _map_agent_roles(request.agents)
        panel = MultiAgentPanel(ConsensusConfig())
        panel_request = PanelReviewRequest(
            content=request.content,
            review_depth=request.depth,
            required_agents=required_agents,
        )
        panel_response = panel.review(panel_request)
        response["multi_agent_results"] = [
            vote.model_dump(mode="json") for vote in panel_response.agent_responses
        ]

    agent_roles = None
    if response.get("multi_agent_results"):
        agent_roles = [vote["role"] for vote in response["multi_agent_results"]]

    analytics_store.append_episode(
        EpisodeRecord(
            session_id=response["id"],
            task_id="sdk_review",
            score=result.score,
            cost_usd=response["cost"],
            steps=1,
            timestamp=datetime.utcnow().isoformat(),
            event_type="review",
            model=response["model_used"],
            agent_roles=agent_roles,
            metadata={"multi_agent": request.multi_agent},
        )
    )

    return response


@router.post("/review/stream")
async def review_stream(request: ReviewRequest):
    if not request.content or not request.content.strip():
        raise HTTPException(status_code=422, detail="Content cannot be empty.")

    def stream():
        for idx, word in enumerate(request.content.split()):
            payload = {"token": word, "index": idx}
            yield json.dumps(payload) + "\n"
        yield json.dumps({"done": True}) + "\n"

    return StreamingResponse(stream(), media_type="application/json")


@router.post("/suggest")
async def suggest(request: SuggestRequest) -> Dict[str, Any]:
    suggestions: List[str] = []
    for flag in request.flags:
        suggestion = flag.get("suggestion") if isinstance(flag, dict) else None
        if suggestion:
            suggestions.append(suggestion)

    if not suggestions:
        suggestions.append("Clarify claims and provide supporting evidence where possible.")

    return {"suggestions": suggestions}


@router.post("/apply")
async def apply(request: ApplyRequest) -> Dict[str, Any]:
    if not request.suggestions:
        return {"improved_content": request.content}

    improvements = "\n".join(f"- {item}" for item in request.suggestions)
    improved = f"{request.content}\n\nRevisions Applied:\n{improvements}"
    analytics_store.append_episode(
        EpisodeRecord(
            session_id=str(uuid.uuid4()),
            task_id="improve",
            score=0.0,
            cost_usd=0.0,
            steps=1,
            timestamp=datetime.utcnow().isoformat(),
            event_type="improve",
            model="verifai-rubric-v1",
            metadata={"suggestions_count": len(request.suggestions)},
        )
    )
    return {"improved_content": improved}


@router.post("/compliance")
async def compliance(request: ComplianceRequest) -> Dict[str, Any]:
    if not request.content or not request.content.strip():
        raise HTTPException(status_code=422, detail="Content cannot be empty.")

    result = _run_compliance(request.content, request.framework)
    analytics_store.append_episode(
        EpisodeRecord(
            session_id=str(uuid.uuid4()),
            task_id="compliance",
            score=result.get("score", 0.0),
            cost_usd=0.0,
            steps=1,
            timestamp=datetime.utcnow().isoformat(),
            event_type="compliance",
            model="verifai-compliance-v1",
            metadata={"framework": request.framework},
        )
    )
    return result


@router.post("/multi-agent")
async def multi_agent(request: MultiAgentRequest) -> Dict[str, Any]:
    if not request.content or not request.content.strip():
        raise HTTPException(status_code=422, detail="Content cannot be empty.")

    required_agents = _map_agent_roles(request.agents)
    panel = MultiAgentPanel(ConsensusConfig())
    panel_request = PanelReviewRequest(
        content=request.content,
        review_depth=request.depth,
        required_agents=required_agents,
    )
    panel_response = panel.review(panel_request)

    analytics_store.append_episode(
        EpisodeRecord(
            session_id=str(uuid.uuid4()),
            task_id="multi_agent",
            score=panel_response.consensus.final_score,
            cost_usd=panel_response.cost,
            steps=1,
            timestamp=datetime.utcnow().isoformat(),
            event_type="multi_agent",
            model="verifai-panel-v1",
            agent_roles=[vote.role.value for vote in panel_response.agent_responses],
            metadata={"strategy": panel_response.consensus.resolution_strategy},
        )
    )

    return {
        "consensus_decision": panel_response.consensus.final_decision,
        "final_score": panel_response.consensus.final_score,
        "consensus_reached": panel_response.consensus.consensus_reached,
        "agent_votes": [
            vote.model_dump(mode="json") for vote in panel_response.agent_responses
        ],
        "disagreements": panel_response.consensus.disagreements,
        "recommendations": panel_response.recommendations,
        "summary": panel_response.summary,
        "cost": panel_response.cost,
    }


@router.get("/cost/report")
@router.get("/cost/report/")
async def cost_report(days: int = 30) -> Dict[str, Any]:
    summary = analytics_store.get_summary_for_days(days)
    total_cost = summary.total_cost
    total_reviews = summary.total_episodes
    average_cost = total_cost / total_reviews if total_reviews else 0.0

    by_task = {task_id: entry.get("total_cost", 0.0) for task_id, entry in summary.by_task.items()}

    return {
        "period_days": days,
        "total_cost": total_cost,
        "total_reviews": total_reviews,
        "average_cost": average_cost,
        "breakdown": {
            "by_model": summary.by_model,
            "by_agent": summary.by_agent,
            "by_task": by_task,
            "total_cost": total_cost,
            "average_cost_per_review": average_cost,
        },
        "efficiency_score": 0.75 if total_reviews else 0.0,
        "optimization_suggestions": [],
        "budget_status": {
            "budget_limit": 0.0,
            "current_cost": total_cost,
            "remaining": 0.0,
            "usage_percentage": 0.0,
            "status": "unknown",
        },
    }


@router.get("/cost/{session_id}")
async def cost_by_session(session_id: str, response: Response) -> Dict[str, Any]:
    """Backward-compatible cost endpoint (moved to /grader/cost/{session_id})."""
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Fri, 30 Jun 2026 23:59:59 GMT"
    response.headers["Link"] = "</grader/cost/{session_id}>; rel=\"successor-version\""
    logger.warning("Deprecated endpoint hit: /cost/%s", session_id)
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    report = session.cost_tracker.get_episode_cost(session_id=session_id)
    return asdict(report)


@router.post("/roi")
async def roi(request: ROIRequest) -> Dict[str, Any]:
    daily_volume = max(0, request.daily_volume)
    cost_per_review = max(0.0, request.cost_per_review)

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
