"""Async usage examples for VerifAI SDK"""

import asyncio
from verifai_sdk import AsyncVerifAIClient


async def async_review_example():
    """Async review example"""
    client = AsyncVerifAIClient(api_key="your-api-key")

    try:
        result = await client.review(
            "The Eiffel Tower is in Berlin.",
            rubric=["factuality"],
        )

        print(f"Score: {result.score}")
        for flag in result.flags:
            print(f"  - {flag.description}")

    finally:
        await client.close()


async def async_batch_example():
    """Async batch review example"""
    client = AsyncVerifAIClient(api_key="your-api-key")

    texts = [
        "Text 1 for review",
        "Text 2 for review",
        "Text 3 for review",
    ] * 10

    try:
        results = await client.batch_review(texts, max_concurrent=5)

        print(f"Processed {results.total_items} items")
        print(f"Successful: {results.successful_items}")
        print(f"Average score: {results.average_score:.3f}")
        print(f"Total cost: ${results.total_cost:.4f}")

    finally:
        await client.close()


async def async_multi_agent_example():
    """Async multi-agent review example"""
    from verifai_sdk.models import AgentRole

    client = AsyncVerifAIClient(api_key="your-api-key")

    try:
        result = await client.multi_agent_review(
            "Sensitive content to review",
            agents=[AgentRole.SAFETY, AgentRole.FACTUALITY],
            depth="deep",
        )

        print(f"Decision: {result.consensus_decision}")
        print(f"Score: {result.final_score:.3f}")

    finally:
        await client.close()


if __name__ == "__main__":
    print("Async VerifAI SDK Examples")
    print("=" * 50)

    asyncio.run(async_review_example())
    asyncio.run(async_batch_example())
    asyncio.run(async_multi_agent_example())
