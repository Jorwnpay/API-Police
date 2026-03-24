"""Batch calibration entrypoint for mainstream Claude/GPT/Gemini models."""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

from api_police.calibrator import FingerprintCalibrator
from api_police.constants import normalize_model_family
from api_police.runner import run_calibration


DEFAULT_MODELS = {
    "official": {
        "claude": [
            "claude-4-6-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
        ],
        "gpt": [
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
        ],
        "gemini": [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
        ],
    },
    "openrouter": {
        "claude": [
            "anthropic/claude-sonnet-4.6",
            "anthropic/claude-opus-4.6",
            "anthropic/claude-haiku-4.5",
        ],
        "gpt": [
            "openai/gpt-4o",
            "openai/gpt-4-turbo",
            "openai/gpt-3.5-turbo",
        ],
        "gemini": [
            "google/gemini-2.5-pro",
            "google/gemini-2.5-flash",
            "google/gemini-2.0-flash",
        ],
    },
}

DEFAULT_BASE_URLS = {
    "official": {
        "claude": "https://api.anthropic.com/v1",
        "gpt": "https://api.openai.com/v1",
        "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    },
    "openrouter": {
        "claude": "https://openrouter.ai/api/v1",
        "gpt": "https://openrouter.ai/api/v1",
        "gemini": "https://openrouter.ai/api/v1",
    },
}


@dataclass
class Target:
    family: str
    model: str
    base_url: str
    api_key: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="api-police-batch-calibrate",
        description="Batch calibrate mainstream Claude/GPT/Gemini models.",
    )
    parser.add_argument(
        "--provider",
        choices=["official", "openrouter"],
        default="openrouter",
        help="Target provider profile (default: openrouter).",
    )
    parser.add_argument(
        "--families",
        default="claude,gpt,gemini",
        help="Comma-separated families to calibrate (default: claude,gpt,gemini).",
    )
    parser.add_argument(
        "--base-url",
        help="Override base URL for all families.",
    )
    parser.add_argument(
        "--api-key",
        help="Override API key for all families.",
    )
    parser.add_argument("--claude-base-url", help="Family-specific base URL.")
    parser.add_argument("--gpt-base-url", help="Family-specific base URL.")
    parser.add_argument("--gemini-base-url", help="Family-specific base URL.")
    parser.add_argument("--claude-api-key", help="Family-specific API key.")
    parser.add_argument("--gpt-api-key", help="Family-specific API key.")
    parser.add_argument("--gemini-api-key", help="Family-specific API key.")
    parser.add_argument("--fingerprint-dir", default="fingerprints", help="Fingerprint directory.")
    parser.add_argument("--timeout", type=float, default=60.0, help="Per-request timeout in seconds.")
    parser.add_argument("--delay-seconds", type=float, default=1.0, help="Delay between models.")
    parser.add_argument("--skip-existing", action="store_true", help="Skip models already calibrated.")
    parser.add_argument(
        "--summary-output",
        default="fingerprints/batch_calibration_summary.json",
        help="Write batch summary JSON to this path.",
    )
    return parser


def _families_from_arg(raw: str) -> list[str]:
    return [normalize_model_family(item.strip()) for item in raw.split(",") if item.strip()]


def _resolve_base_url(args: argparse.Namespace, family: str) -> str:
    family_specific = getattr(args, f"{family}_base_url")
    if family_specific:
        return family_specific
    if args.base_url:
        return args.base_url
    return DEFAULT_BASE_URLS[args.provider][family]


def _resolve_api_key(args: argparse.Namespace, family: str) -> str:
    family_specific = getattr(args, f"{family}_api_key")
    if family_specific:
        return family_specific
    if args.api_key:
        return args.api_key

    env_fallbacks = {
        "claude": ["CLAUDE_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY", "API_POLICE_API_KEY"],
        "gpt": ["OPENAI_API_KEY", "OPENROUTER_API_KEY", "API_POLICE_API_KEY"],
        "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENROUTER_API_KEY", "API_POLICE_API_KEY"],
    }
    for name in env_fallbacks[family]:
        value = os.getenv(name)
        if value:
            return value
    return ""


def _build_targets(args: argparse.Namespace) -> list[Target]:
    families = _families_from_arg(args.families)
    targets: list[Target] = []

    for family in families:
        if family not in DEFAULT_MODELS[args.provider]:
            continue
        base_url = _resolve_base_url(args, family)
        api_key = _resolve_api_key(args, family)
        for model in DEFAULT_MODELS[args.provider][family]:
            targets.append(Target(family=family, model=model, base_url=base_url, api_key=api_key))
    return targets


def _already_calibrated(fingerprint_dir: str) -> set[tuple[str, str]]:
    calibrator = FingerprintCalibrator()
    calibrator.load(fingerprint_dir)

    done: set[tuple[str, str]] = set()
    for family, models in calibrator.fingerprints.items():
        for model_name in models.keys():
            done.add((family, model_name))
    return done


def _write_summary(path: str, summary: dict[str, object]) -> None:
    output_path = Path(path)
    if output_path.parent:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    targets = _build_targets(args)
    if not targets:
        parser.error("No calibration targets resolved. Check --families or --provider.")

    if any(not target.api_key for target in targets):
        missing = sorted({target.family for target in targets if not target.api_key})
        parser.error(
            "Missing API key for families: "
            + ", ".join(missing)
            + ". Provide --api-key/--<family>-api-key or env vars."
        )

    existing = _already_calibrated(args.fingerprint_dir) if args.skip_existing else set()

    total = len(targets)
    started_at = time.time()
    success = 0
    skipped = 0
    failed = 0
    records: list[dict[str, object]] = []

    for index, target in enumerate(targets, start=1):
        if args.skip_existing and (target.family, target.model) in existing:
            skipped += 1
            print(f"[{index}/{total}] SKIP {target.family}/{target.model} (already calibrated)")
            records.append(
                {
                    "family": target.family,
                    "model": target.model,
                    "status": "skipped",
                    "reason": "already calibrated",
                }
            )
            continue

        print(f"[{index}/{total}] START {target.family}/{target.model}")
        try:
            result = run_calibration(
                base_url=target.base_url,
                api_key=target.api_key,
                model_name=target.model,
                model_family=target.family,
                timeout=args.timeout,
                fingerprint_dir=args.fingerprint_dir,
            )
            success += 1
            print(f"[{index}/{total}] DONE  {target.family}/{target.model}")
            records.append(
                {
                    "family": target.family,
                    "model": target.model,
                    "status": "success",
                    "tokenizer_hash": result.get("tokenizer_hash"),
                    "capability_tier": result.get("capability_tier"),
                    "behavior_fingerprint": result.get("behavior_fingerprint"),
                }
            )
        except Exception as exc:
            failed += 1
            print(f"[{index}/{total}] FAIL  {target.family}/{target.model} -> {exc}")
            records.append(
                {
                    "family": target.family,
                    "model": target.model,
                    "status": "failed",
                    "error": str(exc),
                }
            )

        if index < total and args.delay_seconds > 0:
            time.sleep(args.delay_seconds)

    elapsed = round(time.time() - started_at, 2)
    summary = {
        "provider": args.provider,
        "fingerprint_dir": args.fingerprint_dir,
        "elapsed_seconds": elapsed,
        "total": total,
        "success": success,
        "failed": failed,
        "skipped": skipped,
        "records": records,
    }
    _write_summary(args.summary_output, summary)

    print("\nBatch calibration finished")
    print(f"  total={total}, success={success}, failed={failed}, skipped={skipped}, elapsed={elapsed}s")
    print(f"  summary={args.summary_output}")


if __name__ == "__main__":
    main()
