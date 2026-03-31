"""Batch processing example for VerifAI SDK"""

from verifai_sdk import VerifAIClient


def run_batch_example():
    client = VerifAIClient(api_key="your-api-key")

    texts = [
        "Example text 1",
        "Example text 2",
        "Example text 3",
        "Example text 4",
    ]

    results = client.batch_review(texts, max_concurrent=4)

    print(f"Processed {results.total_items} items")
    print(f"Average score: {results.average_score:.3f}")
    print(f"Total cost: ${results.total_cost:.4f}")

    client.close()


if __name__ == "__main__":
    run_batch_example()
