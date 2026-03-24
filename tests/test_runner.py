"""Tests for runner orchestration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from api_police.runner import run_audit


@patch("api_police.runner.APIClient")
@patch("api_police.runner.FingerprintCalibrator")
@patch("api_police.runner.TokenizerTester")
@patch("api_police.runner.CapabilityTester")
@patch("api_police.runner.DirectProbeTester")
def test_run_audit_quick(
    mock_direct,
    mock_capability,
    mock_tokenizer,
    mock_calibrator,
    mock_client,
):
    mk_result = lambda name: MagicMock(name=name, verdict=MagicMock(value="PASS"), confidence=1.0, data={}, details="ok", evidence=[], description="d")

    tok = mk_result("Tokenizer Fingerprint")
    tok.name = "Tokenizer Fingerprint"
    cap = mk_result("Capability Ladder")
    cap.name = "Capability Ladder"
    probe = mk_result("Direct Probes")
    probe.name = "Direct Probes"

    mock_tokenizer.return_value.run.return_value = tok
    mock_capability.return_value.run.return_value = cap
    mock_direct.return_value.run.return_value = probe
    mock_calibrator.return_value.tokenizer_db.return_value = {}

    result = run_audit(
        base_url="https://api.example.com/v1",
        api_key="sk-test",
        claimed_model="gpt-4o",
        mode="quick",
    )

    assert result.mode == "quick"
    assert len(result.test_results) == 3
    assert "confidence" in result.analysis
