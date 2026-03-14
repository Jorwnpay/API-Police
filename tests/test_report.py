"""Tests for the Report class and print_report function."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from api_police.report import Report, print_report
from api_police.testers.base import TestResult, Verdict


def _make_result(name: str, verdict: Verdict, confidence: float) -> TestResult:
    return TestResult(
        name=name,
        verdict=verdict,
        confidence=confidence,
        description="Test description.",
        details="Some details.",
    )


def test_overall_confidence_all_pass():
    results = [
        _make_result("Anthropic Magic String Refusal", Verdict.PASS, 0.9),
        _make_result("Knowledge Cutoff / Factual Accuracy", Verdict.PASS, 0.6),
        _make_result("Reasoning Capability Benchmark", Verdict.PASS, 0.7),
        _make_result("Model Self-Identification", Verdict.PASS, 0.5),
    ]
    report = Report(base_url="https://api.example.com/v1", model="claude-3-5-sonnet-20241022", results=results)
    assert report.overall_confidence == pytest.approx(1.0, abs=0.01)
    assert "AUTHENTIC" in report.overall_verdict


def test_overall_confidence_all_fail():
    results = [
        _make_result("Anthropic Magic String Refusal", Verdict.FAIL, 0.0),
        _make_result("Knowledge Cutoff / Factual Accuracy", Verdict.FAIL, 0.0),
        _make_result("Reasoning Capability Benchmark", Verdict.FAIL, 0.0),
        _make_result("Model Self-Identification", Verdict.FAIL, 0.0),
    ]
    report = Report(base_url="https://api.example.com/v1", model="gpt-4o", results=results)
    assert report.overall_confidence == pytest.approx(0.0, abs=0.01)
    assert "FAKE" in report.overall_verdict


def test_overall_confidence_skipped_tests():
    """Skipped tests should not affect the score."""
    results = [
        _make_result("Anthropic Magic String Refusal", Verdict.SKIP, 0.0),
        _make_result("Knowledge Cutoff / Factual Accuracy", Verdict.PASS, 0.6),
        _make_result("Reasoning Capability Benchmark", Verdict.PASS, 0.7),
        _make_result("Model Self-Identification", Verdict.PASS, 0.5),
    ]
    report = Report(base_url="https://api.example.com/v1", model="gpt-4o", results=results)
    # Score should be computed only on the 3 non-skipped tests
    assert report.overall_confidence == pytest.approx(1.0, abs=0.01)


def test_print_report_does_not_raise():
    results = [
        _make_result("Anthropic Magic String Refusal", Verdict.PASS, 0.9),
        _make_result("Knowledge Cutoff / Factual Accuracy", Verdict.WARN, 0.3),
    ]
    report = Report(base_url="https://api.example.com/v1", model="gpt-4o", results=results)
    # Should not raise any exception.
    print_report(report)
