"""Basic usage examples for VerifAI SDK"""

from verifai_sdk import VerifAIClient
from verifai_sdk.models import ComplianceFramework


def basic_review_example():
    """Basic review example"""
    client = VerifAIClient(api_key="your-api-key")

    result = client.review(
        "The iPhone 15 has 8K video recording capability.",
        rubric=["factuality", "safety"],
    )

    print(f"Score: {result.score}")
    for flag in result.flags:
        print(f"  - {flag.description}")
        if flag.suggestion:
            print(f"    Suggestion: {flag.suggestion}")

    client.close()


def improve_example():
    """Output improvement example"""
    client = VerifAIClient(api_key="your-api-key")

    result = client.review("This product is the best thing ever created!")
    print(f"Original score: {result.score}")

    improved = client.improve(result, max_iterations=3)
    print(f"Improved score: {improved.final_score}")
    print(f"Improvement: +{improved.improvement_delta:.3f}")
    print(f"Improved text: {improved.improved}")

    client.close()


def compliance_example():
    """Compliance check example"""
    client = VerifAIClient(api_key="your-api-key")

    result = client.check_compliance(
        "We collect user emails and IP addresses for marketing purposes.",
        framework=ComplianceFramework.GDPR,
    )

    print(f"GDPR Compliance Score: {result.score:.2f}")
    print(f"Risk Level: {result.risk_level}")

    if result.violations:
        print("Violations found:")
        for v in result.violations:
            print(f"  - {v.description}")

    if result.remediation:
        print("Remediation steps:")
        for r in result.remediation:
            print(f"  - {r}")

    client.close()


def batch_example():
    """Batch review example"""
    client = VerifAIClient(api_key="your-api-key")

    texts = [
        "The product is revolutionary!",
        "We guarantee 100% satisfaction.",
        "Our service is the best in the industry.",
    ]

    results = client.batch_review(texts)

    print(f"Processed {results.total_items} items")
    print(f"Average score: {results.average_score:.3f}")
    print(f"Total cost: ${results.total_cost:.4f}")

    for result in results.results:
        print(f"  - Score: {result.score:.3f} | Flags: {len(result.flags)}")

    client.close()


def multi_agent_example():
    """Multi-agent review example"""
    from verifai_sdk.models import AgentRole

    client = VerifAIClient(api_key="your-api-key")

    result = client.multi_agent_review(
        "This product will change your life!",
        agents=[AgentRole.SAFETY, AgentRole.FACTUALITY, AgentRole.BRAND],
    )

    print(f"Consensus: {result.consensus_decision}")
    print(f"Final Score: {result.final_score:.3f}")

    for vote in result.agent_votes:
        print(f"  {vote.agent_name}: {vote.score:.3f}")

    print("\nRecommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")

    client.close()


if __name__ == "__main__":
    print("VerifAI SDK Examples")
    print("=" * 50)

    # Uncomment examples as needed
    # basic_review_example()
    # improve_example()
    # compliance_example()
    # batch_example()
    # multi_agent_example()
