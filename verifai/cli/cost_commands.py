"""CLI commands for cost tracking and optimization"""

import json
from datetime import datetime, timedelta
from typing import Optional

import click
from tabulate import tabulate

from verifai.environment.cost_tracker import CostTracker, CostAwareActionSelector
from verifai.optimization.cost_optimizer import CostOptimizer
from verifai.optimization.budget_manager import BudgetManager
from verifai.models.cost_models import BudgetConfig, CostEventType


@click.group()
def cost():
    """Cost tracking and optimization commands"""
    pass


@cost.command()
@click.option("--days", "-d", type=int, default=7, help="Time range in days")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def dashboard(days: int, json_output: bool):
    """Show cost dashboard"""
    tracker = CostTracker()

    _generate_sample_data(tracker, days)

    summary = tracker.get_cost_summary(days)
    breakdown = tracker.get_cost_breakdown(days)
    budget_status = tracker.get_budget_status()

    if json_output:
        output = {
            "summary": summary.dict(),
            "breakdown": breakdown.dict(),
            "budget": budget_status,
        }
        click.echo(json.dumps(output, indent=2, default=str))
        return

    click.echo("\n" + "=" * 70)
    click.echo("VerifAI - Cost Dashboard")
    click.echo(f"Last {days} Days")
    click.echo("=" * 70 + "\n")

    click.echo("BUDGET STATUS")
    click.echo("-" * 70)

    usage_bar = "#" * int(budget_status["usage_percentage"] * 20) + "." * (
        20 - int(budget_status["usage_percentage"] * 20)
    )
    click.echo(f"  Budget Limit:      ${budget_status['budget_limit']:.2f}")
    click.echo(f"  Current Cost:      ${budget_status['current_cost']:.2f}")
    click.echo(f"  Remaining:         ${budget_status['remaining']:.2f}")
    click.echo(f"  Usage:             {usage_bar} {budget_status['usage_percentage']:.1%}")
    click.echo(f"  Status:            {budget_status['status'].upper()}")

    click.echo("\nCOST BREAKDOWN BY PURPOSE")
    click.echo("-" * 70)

    if breakdown.by_event_type:
        table_data = []
        for purpose, cost_value in sorted(
            breakdown.by_event_type.items(), key=lambda x: -x[1]
        ):
            percentage = (cost_value / summary.total_cost * 100) if summary.total_cost > 0 else 0
            bar = "#" * int(percentage / 5) + "." * (20 - int(percentage / 5))
            table_data.append([purpose.upper(), f"${cost_value:.2f}", f"{bar} {percentage:.1f}%"])

        click.echo(tabulate(table_data, headers=["Purpose", "Cost", ""], tablefmt="simple"))
    else:
        click.echo("  No data available")

    click.echo("\nCOST BY MODEL")
    click.echo("-" * 70)

    if breakdown.by_model:
        table_data = []
        for model, cost_value in sorted(breakdown.by_model.items(), key=lambda x: -x[1]):
            percentage = (cost_value / summary.total_cost * 100) if summary.total_cost > 0 else 0
            bar = "#" * int(percentage / 5) + "." * (20 - int(percentage / 5))
            table_data.append([model, f"${cost_value:.2f}", f"{bar} {percentage:.1f}%"])

        click.echo(tabulate(table_data, headers=["Model", "Cost", ""], tablefmt="simple"))
    else:
        click.echo("  No data available")

    click.echo("\nEFFICIENCY METRICS")
    click.echo("-" * 70)
    click.echo(f"  Total Reviews:       {summary.total_api_calls}")
    click.echo(f"  Average Cost/Review: ${summary.average_cost_per_review:.3f}")
    click.echo(f"  Total Tokens:        {summary.total_tokens_processed:,}")
    click.echo(f"  Cost Efficiency:     {summary.cost_efficiency_score:.2f}")

    if budget_status["alert_count"] > 0:
        click.echo("\nACTIVE ALERTS")
        click.echo("-" * 70)
        click.echo(f"  {budget_status['alert_count']} alerts active")

    click.echo("\n" + "=" * 70)
    click.echo("Tip: Run 'python -m verifai.cli.cost_commands optimize' for suggestions")
    click.echo("=" * 70 + "\n")


@cost.command()
@click.option("--days", "-d", type=int, default=7, help="Time range in days")
@click.option("--apply", "-a", is_flag=True, help="Apply suggested optimizations")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def optimize(days: int, apply: bool, json_output: bool):
    """Generate cost optimization suggestions"""
    tracker = CostTracker()
    _generate_sample_data(tracker, days)

    optimizer = CostOptimizer(tracker)
    report = optimizer.generate_optimization_report(days, apply_suggestions=apply)

    if json_output:
        click.echo(json.dumps(report.dict(), indent=2, default=str))
        return

    click.echo("\n" + "=" * 70)
    click.echo("VerifAI - Cost Optimization Report")
    click.echo("=" * 70 + "\n")

    click.echo(f"ANALYZING {days} DAYS OF USAGE")
    click.echo("-" * 70)
    click.echo(f"  Total Cost:      ${report.current_costs.total_cost:.2f}")
    click.echo(f"  Total Reviews:   {report.current_costs.total_api_calls}")
    click.echo(f"  Avg Cost/Review: ${report.current_costs.average_cost_per_review:.3f}")
    click.echo(f"  Efficiency:      {report.current_costs.cost_efficiency_score:.2f}")

    click.echo("\nOPTIMIZATION SUGGESTIONS")
    click.echo("-" * 70)

    for i, suggestion in enumerate(report.suggestions[:5], 1):
        click.echo(f"\n{i}. {suggestion.title}")
        click.echo(
            f"   Priority: {suggestion.priority.upper()} | "
            f"Difficulty: {suggestion.implementation_difficulty.upper()}"
        )
        click.echo(f"   {suggestion.description}")
        click.echo(f"   Estimated Savings: ${suggestion.estimated_savings:.2f}")
        click.echo(f"   Quality Impact: {suggestion.estimated_quality_impact:+.2f}")

        if suggestion.action_items:
            click.echo("   Actions:")
            for action in suggestion.action_items[:3]:
                click.echo(f"      - {action}")

    click.echo("\n" + "-" * 70)
    click.echo("\nOPTIMIZATION SUMMARY")
    click.echo("-" * 70)
    click.echo(f"  Current Cost:    ${report.current_costs.total_cost:.2f}")
    click.echo(f"  Projected Cost:  ${report.projected_costs.total_cost:.2f}")
    click.echo(f"  Total Savings:   ${report.total_savings:.2f}")
    click.echo(f"  Savings:         {report.savings_percentage:.1%}")
    click.echo(f"  Quality Impact:  {report.quality_impact:+.2f}")

    if report.total_savings > 0:
        click.echo("\nANNUAL PROJECTION")
        click.echo("-" * 70)
        annual_savings = report.total_savings * 52
        click.echo(f"  Projected Annual Savings: ${annual_savings:.2f}")

    click.echo("\n" + "=" * 70)
    click.echo("Tip: Use --apply to automatically apply these optimizations")
    click.echo("=" * 70 + "\n")


@cost.command()
@click.option("--daily", type=float, help="Daily budget limit")
@click.option("--weekly", type=float, help="Weekly budget limit")
@click.option("--monthly", type=float, help="Monthly budget limit")
@click.option("--alert", type=float, default=0.8, help="Alert threshold (0-1)")
@click.option("--critical", type=float, default=0.95, help="Critical threshold (0-1)")
def set_budget(daily: Optional[float], weekly: Optional[float], monthly: Optional[float], alert: float, critical: float):
    """Set budget limits"""
    config = BudgetConfig(
        daily_budget=daily,
        weekly_budget=weekly,
        monthly_budget=monthly,
        alert_threshold=alert,
        critical_threshold=critical,
    )

    click.echo("\n" + "=" * 70)
    click.echo("VerifAI - Budget Configuration")
    click.echo("=" * 70 + "\n")

    click.echo("Budget Limits:")
    if daily:
        click.echo(f"  Daily:   ${daily:.2f}")
    if weekly:
        click.echo(f"  Weekly:  ${weekly:.2f}")
    if monthly:
        click.echo(f"  Monthly: ${monthly:.2f}")

    click.echo(f"\nAlert Threshold: {alert:.0%}")
    click.echo(f"Critical Threshold: {critical:.0%}")

    click.echo("\nBudget configuration saved")
    click.echo("\n" + "=" * 70 + "\n")


@cost.command()
@click.option("--days", "-d", type=int, default=30, help="Forecast days")
@click.option("--monthly", type=float, help="Monthly budget limit for forecast")
def forecast(days: int, monthly: Optional[float]):
    """Forecast budget usage"""
    tracker = CostTracker()
    _generate_sample_data(tracker, 30)

    config = BudgetConfig(monthly_budget=monthly) if monthly is not None else None
    manager = BudgetManager(tracker, config=config)
    forecast_data = manager.get_budget_forecast(days)

    click.echo("\n" + "=" * 70)
    click.echo("VerifAI - Budget Forecast")
    click.echo("=" * 70 + "\n")

    click.echo(f"Current Spending: ${forecast_data['current_spending']:.2f}")
    click.echo(f"Daily Average: ${forecast_data['daily_average']:.2f}")

    click.echo("\nFORECAST")
    click.echo("-" * 70)

    table_data = []
    for f in forecast_data["forecast"]:
        exceeds = "YES" if f["projected_cost"] > (f["budget_limit"] or float("inf")) else "NO"
        table_data.append(
            [
                f"Day {f['day']}",
                f"${f['projected_cost']:.2f}",
                f"{exceeds} {f['percentage']:.1%}",
            ]
        )

    click.echo(tabulate(table_data, headers=["Period", "Projected Cost", "Usage"], tablefmt="simple"))

    if forecast_data["will_exceed"]:
        click.echo("\nWarning: Budget will be exceeded within the forecast period")

    click.echo("\n" + "=" * 70 + "\n")


def _generate_sample_data(tracker: CostTracker, days: int = 7) -> None:
    """Generate sample cost data for demo purposes"""
    models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "claude-3-opus"]
    event_types = [
        CostEventType.REVIEW,
        CostEventType.REWRITE,
        CostEventType.APPROVAL,
        CostEventType.SUGGESTION,
    ]

    for i in range(days * 20):
        day_offset = i // 20
        _ = datetime.now() - timedelta(days=days - day_offset)

        model = models[i % len(models)]
        event_type = event_types[i % len(event_types)]

        input_tokens = 500 + (i % 1500)
        output_tokens = 100 + (i % 500)

        tracker.log_event(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            event_type=event_type,
            episode_id=i % 10,
            task_id=i % 3,
            latency_ms=100 + (i % 500),
        )

        quality = 0.5 + (i % 50) / 100
        tracker.record_quality(quality)


if __name__ == "__main__":
    cost()
