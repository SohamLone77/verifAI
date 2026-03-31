"""Multi-agent review example"""

from verifai_sdk import VerifAIClient
from verifai_sdk.models import AgentRole


def run_multi_agent_review():
    client = VerifAIClient(api_key="your-api-key")

    result = client.multi_agent_review(
        "This product will change your life!",
        agents=[AgentRole.SAFETY, AgentRole.FACTUALITY, AgentRole.BRAND],
        depth="standard",
    )

    print(f"Decision: {result.consensus_decision}")
    print(f"Final score: {result.final_score:.3f}")

    for vote in result.agent_votes:
        print(f"  {vote.agent_name}: {vote.score:.3f}")

    client.close()


if __name__ == "__main__":
    run_multi_agent_review()
