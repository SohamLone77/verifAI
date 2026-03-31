"""Command-line interface for VerifAI SDK"""

import click
import json
import sys
import os
from typing import Optional
from pathlib import Path

from verifai_sdk.client import VerifAIClient, ClientConfig
from verifai_sdk.models import ComplianceFramework
from verifai_sdk.version import __version__


@click.group()
@click.option("--api-key", envvar="VERIFAI_API_KEY", help="VerifAI API key")
@click.option("--base-url", default="https://api.verifai.ai", help="API base URL")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx, api_key, base_url, verbose):
    """VerifAI CLI - Verify AI, One Output at a Time"""
    ctx.ensure_object(dict)
    ctx.obj["config"] = ClientConfig(
        api_key=api_key,
        base_url=base_url,
        log_level="DEBUG" if verbose else "INFO",
    )
    ctx.obj["verbose"] = verbose


@cli.command()
@click.argument("text")
@click.option("--rubric", "-r", help="Comma-separated rubric dimensions")
@click.option("--compliance", "-c", type=click.Choice([f.value for f in ComplianceFramework]), help="Compliance framework")
@click.option("--multi-agent", "-m", is_flag=True, help="Use multi-agent review")
@click.option("--output", "-o", help="Output file")
@click.option("--json", "-j", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def review(ctx, text, rubric, compliance, multi_agent, output, json_output):
    """Review AI-generated text"""
    client = VerifAIClient(config=ctx.obj["config"])

    try:
        result = client.review(
            text,
            rubric=rubric.split(",") if rubric else None,
            compliance=ComplianceFramework(compliance) if compliance else None,
            multi_agent=multi_agent,
        )

        if json_output:
            output_data = {
                "score": result.score,
                "flags": [f.__dict__ for f in result.flags],
                "rubric_scores": result.rubric_scores,
                "cost": result.cost,
                "latency_ms": result.latency_ms,
            }
            json_str = json.dumps(output_data, indent=2)

            if output:
                with open(output, "w") as f:
                    f.write(json_str)
                click.echo(f"Results saved to {output}")
            else:
                click.echo(json_str)
        else:
            click.echo("\n" + "=" * 70)
            click.echo("                    VerifAI - Review Result")
            click.echo("=" * 70 + "\n")

            click.echo(f"Score: {result.score:.3f}")
            click.echo(f"Cost: ${result.cost:.4f}")
            click.echo(f"Latency: {result.latency_ms:.0f}ms")
            click.echo(f"Model: {result.model_used}")

            if result.flags:
                click.echo("\nIssues Detected:")
                for flag in result.flags:
                    severity_bar = "#" * int(flag.severity * 10) + "." * (10 - int(flag.severity * 10))
                    click.echo(f"  - [{flag.type}] {severity_bar} {flag.severity:.1f}")
                    click.echo(f"    {flag.description}")
                    if flag.suggestion:
                        click.echo(f"    Suggestion: {flag.suggestion}")

            if result.rubric_scores:
                click.echo("\nRubric Scores:")
                for dim, score in result.rubric_scores.items():
                    bar = "#" * int(score * 20) + "." * (20 - int(score * 20))
                    click.echo(f"  {dim:12} {bar} {score:.2f}")

            click.echo("\n" + "=" * 70)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        client.close()


@cli.command()
@click.argument("file")
@click.option("--output", "-o", help="Output file")
@click.option("--max-concurrent", default=5, help="Maximum concurrent requests")
@click.pass_context
def batch(ctx, file, output, max_concurrent):
    """Batch review texts from file (one per line)"""
    if not Path(file).exists():
        click.echo(f"File not found: {file}", err=True)
        sys.exit(1)

    with open(file, "r") as f:
        texts = [line.strip() for line in f if line.strip()]

    if not texts:
        click.echo("No texts found in file", err=True)
        sys.exit(1)

    click.echo(f"Processing {len(texts)} texts...")

    client = VerifAIClient(config=ctx.obj["config"])

    try:
        results = client.batch_review(texts, max_concurrent=max_concurrent)

        click.echo("\nBatch Complete")
        click.echo(f"  Successful: {results.successful_items}/{results.total_items}")
        click.echo(f"  Average Score: {results.average_score:.3f}")
        click.echo(f"  Total Cost: ${results.total_cost:.4f}")
        click.echo(f"  Total Time: {results.total_time_ms:.0f}ms")

        if output:
            with open(output, "w") as f:
                json.dump({
                    "total_items": results.total_items,
                    "successful_items": results.successful_items,
                    "failed_items": results.failed_items,
                    "average_score": results.average_score,
                    "total_cost": results.total_cost,
                    "results": [r.__dict__ for r in results.results],
                    "errors": results.errors,
                }, f, indent=2, default=str)
            click.echo(f"\nResults saved to {output}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        client.close()


@cli.command()
@click.argument("text")
@click.option("--iterations", "-i", default=3, help="Maximum improvement iterations")
@click.option("--output", "-o", help="Output file")
@click.pass_context
def improve(ctx, text, iterations, output):
    """Improve AI-generated text"""
    client = VerifAIClient(config=ctx.obj["config"])

    try:
        click.echo("Reviewing original text...")
        result = client.review(text)
        click.echo(f"Original score: {result.score:.3f}")

        click.echo(f"\nImproving (max {iterations} iterations)...")
        improved = client.improve(result, max_iterations=iterations)

        click.echo("\n" + "=" * 70)
        click.echo("                    VerifAI - Improvement Result")
        click.echo("=" * 70 + "\n")

        click.echo(f"Original Score:  {result.score:.3f}")
        click.echo(f"Improved Score:  {improved.final_score:.3f}")
        click.echo(f"Improvement:     +{improved.improvement_delta:.3f}")
        click.echo(f"Iterations:      {improved.iterations}")
        click.echo(f"Cost:            ${improved.cost:.4f}")

        if improved.changes_made:
            click.echo("\nChanges Made:")
            for change in improved.changes_made[:5]:
                click.echo(f"  - {change}")

        click.echo("\nImproved Text:")
        click.echo("-" * 70)
        click.echo(improved.improved)
        click.echo("-" * 70)

        if output:
            with open(output, "w") as f:
                f.write(improved.improved)
            click.echo(f"\nSaved to {output}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        client.close()


@cli.command()
@click.argument("text")
@click.option("--framework", "-f", required=True, type=click.Choice([f.value for f in ComplianceFramework]), help="Compliance framework")
@click.option("--output", "-o", help="Output file")
@click.pass_context
def compliance(ctx, text, framework, output):
    """Check compliance with regulations"""
    client = VerifAIClient(config=ctx.obj["config"])

    try:
        result = client.check_compliance(
            text,
            framework=ComplianceFramework(framework),
        )

        click.echo("\n" + "=" * 70)
        click.echo(f"           VerifAI - {framework.upper()} Compliance Check")
        click.echo("=" * 70 + "\n")

        click.echo(f"Compliance Score:  {result.score:.2f}")
        click.echo(f"Risk Level:        {result.risk_level.upper()}")
        click.echo(f"Confidence:        {result.confidence:.2f}")

        if result.violations:
            click.echo("\nViolations Detected:")
            for v in result.violations:
                click.echo(f"  - {v.description}")

        if result.remediation:
            click.echo("\nRemediation Steps:")
            for r in result.remediation:
                click.echo(f"  - {r}")

        if output:
            with open(output, "w") as f:
                json.dump({
                    "framework": framework,
                    "score": result.score,
                    "risk_level": result.risk_level,
                    "violations": [v.__dict__ for v in result.violations],
                    "remediation": result.remediation,
                }, f, indent=2)
            click.echo(f"\nResults saved to {output}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        client.close()


@cli.command()
@click.option("--days", "-d", default=30, help="Days to analyze")
@click.option("--json", "-j", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def cost(ctx, days, json_output):
    """Show cost tracking report"""
    client = VerifAIClient(config=ctx.obj["config"])

    try:
        report = client.get_cost_report(days)

        if json_output:
            click.echo(json.dumps(report.__dict__, indent=2, default=str))
        else:
            click.echo("\n" + "=" * 70)
            click.echo("                    VerifAI - Cost Report")
            click.echo(f"                      Last {days} Days")
            click.echo("=" * 70 + "\n")

            click.echo(f"Total Cost:        ${report.total_cost:.2f}")
            click.echo(f"Total Reviews:     {report.total_reviews:,}")
            click.echo(f"Average Cost:      ${report.average_cost:.4f}")
            click.echo(f"Efficiency Score:  {report.efficiency_score:.2f}")

            if report.breakdown.by_model:
                click.echo("\nCost by Model:")
                for model, cost in report.breakdown.by_model.items():
                    bar = "#" * int(cost / report.total_cost * 20) if report.total_cost > 0 else ""
                    click.echo(f"  {model:15} ${cost:.2f} {bar}")

            if report.optimization_suggestions:
                click.echo("\nOptimization Suggestions:")
                for suggestion in report.optimization_suggestions[:3]:
                    click.echo(f"  - {suggestion}")

            if report.budget_status:
                click.echo("\nBudget Status:")
                click.echo(f"  Budget: ${report.budget_status.get('budget_limit', 0):.2f}")
                click.echo(f"  Used:   ${report.budget_status.get('current_cost', 0):.2f}")
                click.echo(f"  Status: {report.budget_status.get('status', 'unknown').upper()}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        client.close()


@cli.command()
@click.option("--daily-volume", "-v", type=int, default=5000, help="Daily review volume")
@click.option("--cost-per-review", "-c", type=float, default=0.05, help="Cost per review")
@click.option("--json", "-j", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def roi(ctx, daily_volume, cost_per_review, json_output):
    """Calculate ROI for VerifAI"""
    client = VerifAIClient(config=ctx.obj["config"])

    try:
        result = client.calculate_roi(daily_volume, cost_per_review)

        if json_output:
            click.echo(json.dumps(result.__dict__, indent=2, default=str))
        else:
            click.echo("\n" + "=" * 70)
            click.echo("                    VerifAI - ROI Calculator")
            click.echo("=" * 70 + "\n")

            click.echo(f"Annual Savings:     ${result.annual_savings:,.0f}")
            click.echo(f"VerifAI Cost:       ${result.verifai_cost:,.0f}")
            click.echo(f"Net Profit:         ${result.net_profit:,.0f}")

            click.echo(f"\nROI:                {result.roi_percentage:.0f}%")
            click.echo(f"Payback Period:     {result.payback_days} days")
            click.echo(f"5-Year Savings:     ${result.five_year_savings:,.0f}")

            if result.recommendations:
                click.echo("\nRecommendations:")
                for rec in result.recommendations:
                    click.echo(f"  - {rec}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        client.close()


@cli.command()
@click.argument("text")
@click.option("--agents", "-a", help="Comma-separated agents (safety,factuality,brand,latency)")
@click.option("--depth", "-d", default="standard", type=click.Choice(["quick", "standard", "deep"]))
@click.option("--output", "-o", help="Output file")
@click.pass_context
def multi_agent(ctx, text, agents, depth, output):
    """Run multi-agent review"""
    client = VerifAIClient(config=ctx.obj["config"])

    agent_list = None
    if agents:
        from verifai_sdk.models import AgentRole

        agent_map = {
            "safety": AgentRole.SAFETY,
            "factuality": AgentRole.FACTUALITY,
            "brand": AgentRole.BRAND,
            "latency": AgentRole.LATENCY,
            "compliance": AgentRole.COMPLIANCE,
        }
        agent_list = [agent_map[a.strip()] for a in agents.split(",") if a.strip() in agent_map]

    try:
        result = client.multi_agent_review(text, agents=agent_list, depth=depth)

        click.echo("\n" + "=" * 70)
        click.echo("                    VerifAI - Multi-Agent Review")
        click.echo("=" * 70 + "\n")

        click.echo(f"Decision:       {result.consensus_decision}")
        click.echo(f"Final Score:    {result.final_score:.3f}")
        click.echo(f"Consensus:      {'Reached' if result.consensus_reached else 'Not reached'}")

        click.echo("\nAgent Votes:")
        for vote in result.agent_votes:
            score_bar = "#" * int(vote.score * 20) + "." * (20 - int(vote.score * 20))
            click.echo(f"  {vote.agent_name:15} {score_bar} {vote.score:.2f} (conf: {vote.confidence:.2f})")

        if result.disagreements:
            click.echo("\nDisagreements:")
            for d in result.disagreements[:3]:
                click.echo(f"  - {d.get('agent_a')} vs {d.get('agent_b')}")

        if result.recommendations:
            click.echo("\nRecommendations:")
            for rec in result.recommendations[:3]:
                click.echo(f"  - {rec}")

        if output:
            with open(output, "w") as f:
                json.dump({
                    "consensus_decision": result.consensus_decision,
                    "final_score": result.final_score,
                    "agent_votes": [v.__dict__ for v in result.agent_votes],
                    "recommendations": result.recommendations,
                    "summary": result.summary,
                }, f, indent=2)
            click.echo(f"\nResults saved to {output}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        client.close()


@cli.command()
def config():
    """Show current configuration"""
    config_data = {
        "api_key": os.environ.get("VERIFAI_API_KEY", "Not set"),
        "base_url": "https://api.verifai.ai",
        "version": __version__,
    }
    click.echo(json.dumps(config_data, indent=2))


if __name__ == "__main__":
    cli()
