"""Tests for the CapabilityTester."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from api_police.testers.base import Verdict
from api_police.testers.capability import CapabilityTester, PROBES


def _make_client_with_answers(answers: list[str]) -> MagicMock:
    client = MagicMock()
    client.chat.side_effect = answers
    return client


def _correct_answers() -> list[str]:
    """Return the expected answers for all PROBES."""
    return [probe.expected for probe in PROBES]


def test_pass_all_correct():
    client = _make_client_with_answers(_correct_answers())
    tester = CapabilityTester(client=client, claimed_model="gpt-4o")
    result = tester.run()
    assert result.verdict == Verdict.PASS
    assert result.confidence > 0


def test_fail_all_wrong():
    wrong = ["TOTALLY WRONG"] * len(PROBES)
    client = _make_client_with_answers(wrong)
    tester = CapabilityTester(client=client, claimed_model="claude-3-5-sonnet-20241022")
    result = tester.run()
    assert result.verdict == Verdict.FAIL
    assert result.confidence == 0.0


def test_api_error_counted_as_failure():
    client = MagicMock()
    client.chat.side_effect = Exception("Connection reset")
    tester = CapabilityTester(client=client, claimed_model="gpt-4o")
    result = tester.run()
    assert result.verdict == Verdict.FAIL


def test_probe_answers_contain_expected():
    """Verify our correct-answer list actually passes each probe check."""
    from api_police.testers.capability import _check_reply
    for probe in PROBES:
        assert _check_reply(probe.expected, probe), (
            f"Expected '{probe.expected}' should pass probe: {probe.question}"
        )
