"""CLI commands for multi-agent panel"""

import json
import time

import click
from tabulate import tabulate

from verifai.agents.multi_agent_panel import MultiAgentPanel
from verifai.models.agent_models import ConsensusConfig, ReviewRequest


@click.group()
def agents():
    """Multi-agent panel commands"""
    pass


@agents.command()
@click.argument("content")
@click.option("--depth", "-d", type=click.Choice(["quick", "standard", "deep"]), default="standard")
@click.option(
    "--strategy",
    "-s",
    type=click.Choice(["weighted_voting", "majority", "unanimous"]),
    default="weighted_voting",
)
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def review(content: str, depth: str, strategy: str, json_output: bool):
    """Run multi-agent review on content"""
    click.echo("\n" + "=" * 70)
    click.echo("VerifAI - Multi-Agent Review")
    click.echo("=" * 70 + "\n")

    click.echo(f"Content: {content[:100]}...")
    click.echo(f"Depth: {depth.upper()} | Strategy: {strategy}")

    config = ConsensusConfig(strategy=strategy)
    request = ReviewRequest(content=content, review_depth=depth, consensus_config=config)

    panel = MultiAgentPanel(config)

    with click.progressbar(length=100, label="Agents analyzing") as bar:
        for _ in range(100):
            time.sleep(0.02)
            bar.update(1)

    response = panel.review(request)

    if json_output:
        click.echo(json.dumps(response.dict(), indent=2, default=str))
        return

    click.echo("\n" + "-" * 70)
    click.echo("CONSENSUS RESULT")
    click.echo("-" * 70)
    click.echo(f"  Decision: {response.consensus.final_decision}")
    click.echo(f"  Score: {response.consensus.final_score:.2f}")
    click.echo(f"  Confidence: {response.consensus.confidence:.2f}")
    click.echo(
        f"  Consensus Reached: {'YES' if response.consensus.consensus_reached else 'NO'}"
    )

    click.echo("\nAGENT VOTES")
    click.echo("-" * 70)

    table_data = []
    for vote in response.agent_responses:
        score_bar = "#" * int(vote.score * 20) + "." * (20 - int(vote.score * 20))
        table_data.append(
            [
                vote.agent_name,
                f"{vote.score:.2f} {score_bar}",
                f"{vote.confidence:.2f}",
                vote.reasoning[:50] + "...",
            ]
        )

    click.echo(
        tabulate(
            table_data,
            headers=["Agent", "Score", "Confidence", "Reasoning"],
            tablefmt="simple",
        )
    )

    if response.consensus.disagreements:
        click.echo("\nDISAGREEMENTS DETECTED")
        click.echo("-" * 70)
        for disagreement in response.consensus.disagreements:
            click.echo(
                f"  - {disagreement['agent_a']} ({disagreement['score_a']:.2f}) "
                f"vs {disagreement['agent_b']} ({disagreement['score_b']:.2f})"
            )

    click.echo("\nRECOMMENDATIONS")
    click.echo("-" * 70)
    for rec in response.recommendations:
        click.echo(f"  - {rec}")

    click.echo("\nMETRICS")
    click.echo("-" * 70)
    click.echo(f"  Processing Time: {response.processing_time_ms:.0f} ms")
    click.echo(f"  Tokens Used: {response.tokens_used:,}")
    click.echo(f"  Estimated Cost: ${response.cost:.4f}")

    click.echo("\n" + "=" * 70 + "\n")


@agents.command()
def performance():
    """Show agent performance metrics"""
    panel = MultiAgentPanel()
    performance_data = panel.get_agent_performance()

    click.echo("\n" + "=" * 70)
    click.echo("VerifAI - Agent Performance")
    click.echo("=" * 70 + "\n")

    table_data = []
    for agent_name, metrics in performance_data.items():
        table_data.append(
            [
                agent_name.replace("_", " ").title(),
                metrics["metrics"]["total_reviews"],
                f"{metrics['metrics']['average_score']:.2f}",
                f"{metrics['metrics']['average_confidence']:.2f}",
                f"{metrics['metrics']['average_latency_ms']:.0f}ms",
            ]
        )

    click.echo(
        tabulate(
            table_data,
            headers=["Agent", "Reviews", "Avg Score", "Avg Confidence", "Latency"],
            tablefmt="grid",
        )
    )

    click.echo("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    agents()
