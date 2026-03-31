from verifai_sdk.models import Issue, ReviewResult, AgentVote, AgentRole, MultiAgentResult


def test_issue_defaults():
    issue = Issue(type="factuality", severity=0.5, description="Test issue")
    assert issue.confidence == 0.8


def test_review_result_fields():
    review = ReviewResult(
        id="r1",
        original_output="text",
        score=0.9,
        flags=[],
        rubric_scores={"safety": 0.95},
    )
    assert review.score == 0.9
    assert review.rubric_scores["safety"] == 0.95


def test_multi_agent_result():
    vote = AgentVote(
        agent_name="SafetyGuard",
        role=AgentRole.SAFETY,
        score=0.8,
        confidence=0.9,
        reasoning="Looks safe",
    )
    result = MultiAgentResult(
        consensus_decision="APPROVED",
        final_score=0.8,
        consensus_reached=True,
        agent_votes=[vote],
        disagreements=[],
        recommendations=[],
        summary="All good",
        processing_time_ms=12.3,
        cost=0.01,
    )
    assert result.consensus_decision == "APPROVED"
