"""Tests for KnowledgeCutoffTester."""

from __future__ import annotations

from unittest.mock import MagicMock

from api_police.testers.base import Verdict
from api_police.testers.knowledge import KnowledgeCutoffTester


def test_knowledge_pass_with_expected_answers():
    client = MagicMock()
    client.chat.side_effect = [
        "Chiefs",
        "Trump",
        "OpenAI",
        "I am gpt-4o.",
    ]

    tester = KnowledgeCutoffTester(client=client, claimed_model="gpt-4o")
    result = tester.run()

    assert result.verdict in (Verdict.PASS, Verdict.WARN)
    assert result.data["ratio"] >= 0.5


def test_knowledge_fail_with_wrong_answers():
    client = MagicMock()
    client.chat.side_effect = ["unknown", "unknown", "unknown", "unknown"]

    tester = KnowledgeCutoffTester(client=client, claimed_model="gpt-4o")
    result = tester.run()

    assert result.verdict == Verdict.FAIL
    assert result.confidence == 0.0
