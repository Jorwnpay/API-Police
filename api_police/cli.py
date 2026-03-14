"""Command-line interface for API Police."""

from __future__ import annotations

import argparse
import sys

from api_police.report import print_report
from api_police.runner import run_all


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="api-police",
        description=(
            "API Police – verify whether an AI API endpoint truly uses the claimed model.\n\n"
            "Example:\n"
            "  api-police --base-url https://api.openai.com/v1 \\\n"
            "              --api-key sk-... \\\n"
            "              --model gpt-4o"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--base-url",
        required=True,
        metavar="URL",
        help="Base URL of the OpenAI-compatible API endpoint (e.g. https://api.openai.com/v1).",
    )
    parser.add_argument(
        "--api-key",
        required=True,
        metavar="KEY",
        help="API key for the endpoint.",
    )
    parser.add_argument(
        "--model",
        required=True,
        metavar="MODEL",
        help="Model name as advertised by the provider (e.g. gpt-4o, claude-3-5-sonnet-20241022).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="Per-request timeout in seconds (default: 60).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress messages while running tests.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    report = run_all(
        base_url=args.base_url,
        api_key=args.api_key,
        model=args.model,
        timeout=args.timeout,
        verbose=args.verbose,
    )
    print_report(report)

    # Exit with non-zero code when the verdict is not AUTHENTIC.
    if "AUTHENTIC" not in report.overall_verdict:
        sys.exit(1)


if __name__ == "__main__":
    main()
