from verifai_sdk.client import VerifAIClient
from verifai_sdk.models import ClientConfig


def test_review_maps_response(monkeypatch):
    client = VerifAIClient(api_key="test_key_12345", config=ClientConfig(cache_enabled=False))

    def fake_request(method, endpoint, data=None, use_cache=True):
        if endpoint == "review":
            return {
                "id": "r1",
                "score": 0.5,
                "flags": [],
                "rubric_scores": {"safety": 0.9},
                "cost": 0.01,
                "tokens_used": 10,
                "model_used": "gpt-4",
            }
        return {}

    monkeypatch.setattr(client, "_request", fake_request)

    result = client.review("hello")
    assert result.score == 0.5
    assert result.rubric_scores["safety"] == 0.9


def test_multi_agent_review(monkeypatch):
    client = VerifAIClient(api_key="test_key_12345", config=ClientConfig(cache_enabled=False))

    def fake_request(method, endpoint, data=None, use_cache=True):
        if endpoint == "multi-agent":
            return {
                "consensus_decision": "APPROVED",
                "final_score": 0.9,
                "consensus_reached": True,
                "agent_votes": [
                    {
                        "agent_name": "SafetyGuard",
                        "role": "safety_expert",
                        "score": 0.9,
                        "confidence": 0.8,
                        "reasoning": "Safe",
                        "flags": [],
                        "suggestions": [],
                        "processing_time_ms": 1.0,
                    }
                ],
                "disagreements": [],
                "recommendations": [],
                "summary": "All good",
                "cost": 0.01,
            }
        return {}

    monkeypatch.setattr(client, "_request", fake_request)

    result = client.multi_agent_review("hello")
    assert result.consensus_decision == "APPROVED"
    assert result.final_score == 0.9
