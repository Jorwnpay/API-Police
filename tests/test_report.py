"""Tests for report rendering/serialization."""

from __future__ import annotations

import json

from api_police.report import print_report, write_report_json
from api_police.runner import AuditResult
from api_police.testers.base import TestResult, Verdict


def _make_result(name: str, verdict: Verdict, confidence: float) -> TestResult:
    return TestResult(
        name=name,
        verdict=verdict,
        confidence=confidence,
        description="desc",
        details="details",
    )


def _make_audit() -> AuditResult:
    return AuditResult(
        base_url="https://api.example.com/v1",
        claimed_model="gpt-4o",
        mode="quick",
        test_results=[
            _make_result("Tokenizer Fingerprint", Verdict.PASS, 1.0),
            _make_result("Capability Ladder", Verdict.WARN, 0.5),
        ],
        analysis={
            "verdict": "⚠️ SUSPICIOUS (可疑)",
            "confidence": 62.5,
            "dimension_scores": {"Tokenizer Fingerprint": 1.0, "Capability Ladder": 0.5},
            "flags": ["sample flag"],
            "recommendation": "sample recommendation",
        },
    )


def test_print_report_does_not_raise():
    report = _make_audit()
    print_report(report)


def test_write_report_json(tmp_path):
    report = _make_audit()
    target = tmp_path / "report.json"
    write_report_json(report, str(target))

    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["analysis"]["confidence"] == 62.5
    assert payload["claimed_model"] == "gpt-4o"
