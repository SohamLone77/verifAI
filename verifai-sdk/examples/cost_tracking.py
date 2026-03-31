"""Cost tracking example"""

from verifai_sdk import VerifAIClient


def run_cost_report():
    client = VerifAIClient(api_key="your-api-key")

    report = client.get_cost_report(days=30)

    print(f"Total cost: ${report.total_cost:.2f}")
    print(f"Total reviews: {report.total_reviews}")
    print(f"Average cost: ${report.average_cost:.4f}")

    if report.optimization_suggestions:
        print("Suggestions:")
        for suggestion in report.optimization_suggestions[:3]:
            print(f"  - {suggestion}")

    client.close()


if __name__ == "__main__":
    run_cost_report()
