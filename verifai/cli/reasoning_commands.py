"""CLI commands for Chain-of-Thought reasoning"""

import json
import click

from verifai.environment.chain_of_thought import ReasoningEngine, ReasoningQualityScorer
from verifai.models.reasoning_models import ReasoningRequest, ReasoningChain


@click.group()
def reason():
    """Chain-of-Thought reasoning commands"""
    pass


@reason.command()
@click.argument("query")
@click.option(
    "--depth",
    "-d",
    type=click.Choice(["shallow", "medium", "deep"]),
    default="medium",
    help="Reasoning depth",
)
@click.option("--threshold", "-t", type=float, default=0.7, help="Confidence threshold")
@click.option("--show-reasoning", "-s", is_flag=True, help="Show full reasoning chain")
@click.option("--output", "-o", type=click.Path(), help="Output file")
@click.option("--json-output", "-j", is_flag=True, help="Print JSON output")
def analyze(
    query: str,
    depth: str,
    threshold: float,
    show_reasoning: bool,
    output: str,
    json_output: bool,
):
    """Analyze a query with Chain-of-Thought reasoning"""
    click.echo("\n" + "=" * 70)
    click.echo("VerifAI - Chain-of-Thought Reasoning")
    click.echo("=" * 70 + "\n")

    click.echo(f"Query: {query}")
    click.echo(f"Depth: {depth.upper()} | Threshold: {threshold:.0%}")

    engine = ReasoningEngine()

    request = ReasoningRequest(
        query=query,
        reasoning_depth=depth,
        confidence_threshold=threshold,
        include_alternatives=True,
        detect_contradictions=True,
    )

    click.echo("\n" + "-" * 70)
    click.echo("Generating reasoning chain...")

    with click.progressbar(length=100, label="Reasoning") as bar:
        for _ in range(100):
            bar.update(1)

    response = engine.reason(request)

    if not response.success or not response.reasoning_chain:
        click.echo(f"\nError: {response.error}")
        return

    chain = response.reasoning_chain

    click.echo("\n" + "-" * 70)
    click.echo("REASONING CHAIN")
    click.echo("-" * 70)

    for step in chain.steps:
        click.echo(f"\nStep {step.step_id}: {step.step_type.value.upper()}")
        click.echo(f"  Reasoning: {step.reasoning[:150]}...")
        click.echo(f"  -> {step.conclusion}")
        click.echo(f"  Confidence: {step.confidence:.2f}")

        if show_reasoning and step.evidence:
            click.echo("  Evidence:")
            for ev in step.evidence[:2]:
                click.echo(f"    - {ev.content} (conf: {ev.confidence:.2f})")

        if show_reasoning and step.alternatives_considered:
            click.echo(f"  Alternatives: {', '.join(step.alternatives_considered[:2])}")

    if chain.contradictions:
        click.echo("\nCONTRADICTIONS DETECTED")
        click.echo("-" * 70)
        for contra in chain.contradictions:
            click.echo(f"  - Step {contra.step_a_id} vs Step {contra.step_b_id}")
            click.echo(f"    {contra.statement_a[:50]}")
            click.echo(f"    {contra.statement_b[:50]}")
            click.echo(f"    Severity: {contra.severity:.2f}")

    scorer = ReasoningQualityScorer()
    quality = scorer.score(chain)

    click.echo("\nQUALITY METRICS")
    click.echo("-" * 70)

    def quality_bar(score: float, label: str) -> None:
        filled = int(score * 20)
        bar = "#" * filled + "." * (20 - filled)
        click.echo(f"  {label:18} {bar} {score:.2f}")

    quality_bar(quality.logical_consistency, "Logical Consistency:")
    quality_bar(quality.evidence_support, "Evidence Support:")
    quality_bar(quality.completeness, "Completeness:")
    quality_bar(quality.clarity, "Clarity:")
    quality_bar(quality.conciseness, "Conciseness:")
    click.echo()
    quality_bar(quality.overall_score, "OVERALL:")

    if quality.strengths:
        click.echo("\nStrengths:")
        for strength in quality.strengths:
            click.echo(f"  - {strength}")

    if quality.issues:
        click.echo("\nIssues:")
        for issue in quality.issues:
            click.echo(f"  - {issue}")

    click.echo("\n" + "-" * 70)
    click.echo("FINAL DECISION")
    click.echo("-" * 70)
    click.echo(f"  {chain.final_decision}")
    click.echo(f"  Confidence: {chain.final_confidence:.2f}")
    click.echo(f"  Processing: {response.processing_time_ms:.0f} ms")

    click.echo("\nEXPLANATION")
    click.echo("-" * 70)
    click.echo(f"  {chain.explanation[:300]}...")

    output_path = output or "reasoning_output.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chain.to_json(), f, indent=2)
    click.echo(f"\nSaved to: {output_path}")

    if json_output:
        click.echo("\nJSON OUTPUT")
        click.echo("-" * 70)
        click.echo(json.dumps(chain.to_json(), indent=2))

    click.echo("\n" + "=" * 70)
    click.echo("Tip: Use --show-reasoning to see full reasoning details")
    click.echo("=" * 70 + "\n")


@reason.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--format", "-f", type=click.Choice(["json", "markdown"]), default="markdown")
def export(file: str, format: str):
    """Export reasoning chain to file"""
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)

    chain = ReasoningChain(**data)

    if format == "markdown":
        output = chain.to_markdown()
        output_file = file.replace(".json", ".md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        click.echo(f"Exported to {output_file}")
    else:
        click.echo(json.dumps(chain.to_json(), indent=2))


@reason.command()
@click.argument("file", type=click.Path(exists=True))
def validate(file: str):
    """Validate reasoning chain consistency"""
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)

    chain = ReasoningChain(**data)

    click.echo("\n" + "=" * 70)
    click.echo("VerifAI - Reasoning Validation")
    click.echo("=" * 70 + "\n")

    click.echo(f"Chain ID: {chain.chain_id[:8]}")
    click.echo(f"Query: {chain.query}")
    click.echo(f"Steps: {len(chain.steps)}")
    click.echo(f"Decision: {chain.final_decision}")
    click.echo(f"Confidence: {chain.final_confidence:.2f}")

    click.echo("\nCONSISTENCY CHECK")
    click.echo("-" * 70)

    if chain.consistency_score > 0.8:
        click.echo("  High consistency - no major contradictions")
    elif chain.consistency_score > 0.5:
        click.echo("  Moderate consistency - some contradictions")
    else:
        click.echo("  Low consistency - significant contradictions")

    step_types = [s.step_type.value for s in chain.steps]
    missing_types = []

    expected = ["observation", "analysis", "synthesis", "decision"]
    for exp in expected:
        if exp not in step_types:
            missing_types.append(exp)

    if missing_types:
        click.echo(f"\nMissing steps: {', '.join(missing_types)}")
    else:
        click.echo("\nComplete reasoning structure")

    steps_with_evidence = sum(1 for s in chain.steps if s.evidence)
    evidence_ratio = steps_with_evidence / len(chain.steps) if chain.steps else 0

    if evidence_ratio > 0.5:
        click.echo(f"\nGood evidence support ({evidence_ratio:.0%} of steps have evidence)")
    else:
        click.echo(f"\nLow evidence support ({evidence_ratio:.0%} of steps have evidence)")

    click.echo("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    reason()
