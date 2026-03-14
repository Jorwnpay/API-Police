"""Core runner that orchestrates all testers."""

from __future__ import annotations

from api_police.client import APIClient
from api_police.report import Report
from api_police.testers import (
    CapabilityTester,
    IdentityTester,
    KnowledgeCutoffTester,
    MagicStringTester,
)


def run_all(
    base_url: str,
    api_key: str,
    model: str,
    timeout: float = 60.0,
    verbose: bool = False,
) -> Report:
    """Run all verification tests and return a consolidated Report.

    Parameters
    ----------
    base_url:
        The base URL of the OpenAI-compatible API endpoint.
    api_key:
        The API key to authenticate with the endpoint.
    model:
        The model name as claimed by the provider.
    timeout:
        Per-request timeout in seconds.
    verbose:
        If True, print progress messages during the run.
    """
    from rich.console import Console

    console = Console()
    client = APIClient(base_url=base_url, api_key=api_key, model=model, timeout=timeout)

    tester_classes = [
        MagicStringTester,
        KnowledgeCutoffTester,
        CapabilityTester,
        IdentityTester,
    ]

    results = []
    for cls in tester_classes:
        tester = cls(client=client, claimed_model=model)
        if verbose:
            console.print(f"[cyan]Running:[/cyan] {tester.name} …", end=" ")
        result = tester.run()
        results.append(result)
        if verbose:
            console.print(f"{result.emoji} {result.verdict.value}")

    return Report(base_url=base_url, model=model, results=results)
