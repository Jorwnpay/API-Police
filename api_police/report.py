"""Report rendering and serialization helpers."""

from __future__ import annotations

import json
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from api_police.runner import AuditResult

console = Console()


def print_report(report: AuditResult) -> None:
    analysis = report.analysis

    console.print()
    console.print(
        Panel(
            "\n".join(
                [
                    "[bold]API Police 验证报告[/bold]",
                    f"Endpoint : [cyan]{report.base_url}[/cyan]",
                    f"Claimed  : [cyan]{report.claimed_model}[/cyan]",
                    f"Mode     : [cyan]{report.mode}[/cyan]",
                ]
            ),
            box=box.DOUBLE_EDGE,
            expand=False,
        )
    )

    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    table.add_column("Layer", style="bold")
    table.add_column("Result", justify="center")
    table.add_column("Confidence", justify="right")
    table.add_column("Details")

    for result in report.test_results:
        verdict = f"{result.emoji} {result.verdict.value}"
        table.add_row(result.name, verdict, f"{result.confidence:.0%}", result.details)

    console.print(table)

    flags = analysis.get("flags", [])
    if flags:
        console.print("\n[bold underline]发现的问题[/bold underline]")
        for flag in flags:
            console.print(f"  {flag}")

    dimension_scores = analysis.get("dimension_scores", {})
    if dimension_scores:
        console.print("\n[bold underline]维度评分[/bold underline]")
        for name, score in dimension_scores.items():
            console.print(f"  - {name}: {score:.0%}")

    confidence = analysis.get("confidence", 0.0)
    verdict = analysis.get("verdict", "N/A")

    color = "green" if "GENUINE" in verdict else "yellow" if "SUSPICIOUS" in verdict else "red"
    console.print()
    console.print(
        Panel(
            f"Overall Confidence: [{color}]{confidence}%[/{color}]\n"
            f"Verdict: [{color}]{verdict}[/{color}]\n"
            f"Recommendation: {analysis.get('recommendation', '')}",
            box=box.DOUBLE_EDGE,
            border_style=color,
            expand=False,
        )
    )
    console.print()


def write_report_json(report: AuditResult, output_path: str) -> None:
    payload = {
        "base_url": report.base_url,
        "claimed_model": report.claimed_model,
        "mode": report.mode,
        "analysis": report.analysis,
        "tests": [
            {
                "name": item.name,
                "verdict": item.verdict.value,
                "confidence": item.confidence,
                "description": item.description,
                "details": item.details,
                "evidence": item.evidence,
                "data": item.data,
            }
            for item in report.test_results
        ],
    }

    path = Path(output_path)
    if path.parent:
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
