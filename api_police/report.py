"""Report generation – aggregates test results and prints a rich summary."""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from api_police.testers.base import TestResult, Verdict

console = Console()


@dataclass
class Report:
    """Aggregated result of all tests."""

    base_url: str
    model: str
    results: list[TestResult]

    @property
    def overall_confidence(self) -> float:
        """Weighted authenticity confidence score in [0, 1]."""
        active = [r for r in self.results if r.verdict != Verdict.SKIP]
        if not active:
            return 0.0
        # Sum passed confidence contributions and normalise by max possible.
        max_possible = sum(
            _max_confidence(r.name) for r in active
        )
        if max_possible == 0.0:
            return 0.0
        total = sum(r.confidence for r in active)
        return min(total / max_possible, 1.0)

    @property
    def overall_verdict(self) -> str:
        score = self.overall_confidence
        if score >= 0.75:
            return "AUTHENTIC ✅"
        elif score >= 0.45:
            return "SUSPICIOUS ⚠️"
        else:
            return "LIKELY FAKE ❌"

    @property
    def overall_verdict_color(self) -> str:
        score = self.overall_confidence
        if score >= 0.75:
            return "green"
        elif score >= 0.45:
            return "yellow"
        else:
            return "red"


# Map from tester name → its maximum possible confidence contribution.
# These must match what each tester returns on a clean PASS.
_MAX_CONFIDENCE_MAP: dict[str, float] = {
    "Anthropic Magic String Refusal": 0.9,
    "Knowledge Cutoff / Factual Accuracy": 0.6,
    "Reasoning Capability Benchmark": 0.7,
    "Model Self-Identification": 0.5,
}


def _max_confidence(name: str) -> float:
    return _MAX_CONFIDENCE_MAP.get(name, 0.5)


def print_report(report: Report) -> None:
    """Print a formatted report to the terminal."""
    console.print()
    console.print(
        Panel(
            f"[bold]API Police Report[/bold]\n"
            f"Endpoint : [cyan]{report.base_url}[/cyan]\n"
            f"Model    : [cyan]{report.model}[/cyan]",
            box=box.DOUBLE_EDGE,
            expand=False,
        )
    )

    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    table.add_column("Test", style="bold", no_wrap=True)
    table.add_column("Result", justify="center")
    table.add_column("Confidence", justify="right")
    table.add_column("Details")

    for result in report.results:
        verdict_str = f"{result.emoji} {result.verdict.value}"
        conf_str = f"{result.confidence:.0%}" if result.verdict != Verdict.SKIP else "N/A"
        table.add_row(result.name, verdict_str, conf_str, result.details)

    console.print(table)

    # Evidence details
    for result in report.results:
        if result.evidence:
            console.print(f"\n[bold underline]{result.name} – Evidence[/bold underline]")
            for ev in result.evidence[:5]:  # limit output
                console.print(f"  [dim]{ev}[/dim]")

    # Overall verdict
    score = report.overall_confidence
    color = report.overall_verdict_color
    console.print()
    console.print(
        Panel(
            f"Overall Authenticity Score: [{color}]{score:.0%}[/{color}]\n"
            f"Verdict: [{color}]{report.overall_verdict}[/{color}]",
            box=box.DOUBLE_EDGE,
            expand=False,
            border_style=color,
        )
    )
    console.print()
