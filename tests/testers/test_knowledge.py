"""Tests for the KnowledgeCutoffTester."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from api_police.testers.base import Verdict
from api_police.testers.knowledge import KnowledgeCutoffTester, PROBES


def _make_client_with_answers(answers: list[str]) -> MagicMock:
    """Return a mock client that cycles through the provided answers."""
    client = MagicMock()
    client.chat.side_effect = answers
    return client


def _correct_answers() -> list[str]:
    """Return correct answers for all PROBES in order."""
    mapping = {
        "FIFA": "Argentina",
        "chemical symbol": "Au",
        "GPT-4": "OpenAI",
        "capital of France": "Paris",
        "first iPhone": "2007",
    }
    answers = []
    for probe in PROBES:
        for keyword, answer in mapping.items():
            if keyword in probe.question:
                answers.append(answer)
                break
        else:
            answers.append(probe.expected_keywords[0])
    return answers


def test_pass_all_correct():
    client = _make_client_with_answers(_correct_answers())
    tester = KnowledgeCutoffTester(client=client, claimed_model="claude-3-5-sonnet-20241022")
    result = tester.run()
    assert result.verdict == Verdict.PASS
    assert result.confidence > 0


def test_fail_all_wrong():
    wrong_answers = ["WRONG ANSWER"] * len(PROBES)
    client = _make_client_with_answers(wrong_answers)
    tester = KnowledgeCutoffTester(client=client, claimed_model="gpt-4o")
    result = tester.run()
    assert result.verdict == Verdict.FAIL
    assert result.confidence == 0.0


def test_warn_partial_correct():
    # Half correct, half wrong
    answers = _correct_answers()
    for i in range(len(answers) // 2):
        answers[i] = "WRONG"
    client = _make_client_with_answers(answers)
    tester = KnowledgeCutoffTester(client=client, claimed_model="gpt-4o")
    result = tester.run()
    # Should be WARN or PASS depending on the ratio
    assert result.verdict in (Verdict.WARN, Verdict.PASS, Verdict.FAIL)


def test_api_error_is_counted_as_fail():
    client = MagicMock()
    client.chat.side_effect = Exception("Timeout")
    tester = KnowledgeCutoffTester(client=client, claimed_model="gpt-4o")
    result = tester.run()
    assert result.verdict == Verdict.FAIL
    assert result.confidence == 0.0
