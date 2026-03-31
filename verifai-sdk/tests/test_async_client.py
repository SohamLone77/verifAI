import asyncio

from verifai_sdk.async_client import AsyncVerifAIClient
from verifai_sdk.models import ClientConfig


def test_async_review_maps_response():
    async def run():
        client = AsyncVerifAIClient(api_key="test_key_12345", config=ClientConfig())

        async def fake_request(method, endpoint, data=None):
            if endpoint == "review":
                return {
                    "id": "r1",
                    "score": 0.7,
                    "flags": [],
                    "rubric_scores": {},
                    "cost": 0.02,
                    "tokens_used": 12,
                    "model_used": "gpt-4",
                }
            return {}

        client._request = fake_request
        result = await client.review("hello")
        await client.close()
        assert result.score == 0.7

    asyncio.run(run())
