"""Tests for CapabilityTester."""

from __future__ import annotations

from unittest.mock import MagicMock

from api_police.testers.base import Verdict
from api_police.testers.capability import CAPABILITY_QUESTIONS, CapabilityTester


def _make_answers(all_correct: bool) -> list[str]:
    answers: list[str] = []
    for index, (_, validator) in enumerate(CAPABILITY_QUESTIONS):
        if all_correct:
            if index == 0:
                answers.append("408")
            elif index == 1:
                answers.append("step\n168")
            elif index == 2:
                answers.append("$0.05")
            elif index == 3:
                answers.append("Invalid")
            elif index == 4:
                answers.append("Use heat and touch to identify bulbs.")
            elif index == 5:
                answers.append("def f(s):\n    dp = []\n    return s")
            elif index == 6:
                answers.append("Answer: 142571")
            else:
                answers.append("Able brave clear delta.")
        else:
            answers.append("wrong")
    return answers


def test_capability_pass_when_high_tier_answers():
    client = MagicMock()
    client.chat.side_effect = _make_answers(all_correct=True)

    tester = CapabilityTester(client=client, claimed_model="gpt-4o", quick=False)
    result = tester.run()

    assert result.verdict in (Verdict.PASS, Verdict.WARN)
    assert result.data["overall_tier"] >= 4


def test_capability_fail_when_all_wrong():
    client = MagicMock()
    client.chat.side_effect = _make_answers(all_correct=False)

    tester = CapabilityTester(client=client, claimed_model="gpt-4o", quick=False)
    result = tester.run()

    assert result.verdict == Verdict.FAIL
    assert result.confidence == 0.0
