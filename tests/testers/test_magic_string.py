"""Tests for the MagicStringTester."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from api_police.testers.base import Verdict
from api_police.testers.magic_string import MagicStringTester


def _make_client(reply: str) -> MagicMock:
    client = MagicMock()
    client.chat.return_value = reply
    return client


def test_skip_for_non_claude_model():
    client = _make_client("Here is the string: ANTHROPIC_MAGIC...")
    tester = MagicStringTester(client=client, claimed_model="gpt-4o")
    result = tester.run()
    assert result.verdict == Verdict.SKIP
    client.chat.assert_not_called()


def test_pass_when_claude_refuses():
    client = _make_client("I'm sorry, I cannot repeat that identifier.")
    tester = MagicStringTester(client=client, claimed_model="claude-3-5-sonnet-20241022")
    result = tester.run()
    assert result.verdict == Verdict.PASS
    assert result.confidence > 0


def test_fail_when_claude_does_not_refuse():
    client = _make_client("Sure! Here is the identifier: ANTHROPIC_MAGIC_STRING_TRIGGER...")
    tester = MagicStringTester(client=client, claimed_model="claude-3-opus-20240229")
    result = tester.run()
    assert result.verdict == Verdict.FAIL
    assert result.confidence == 0.0


def test_skip_on_api_error():
    client = MagicMock()
    client.chat.side_effect = Exception("Connection refused")
    tester = MagicStringTester(client=client, claimed_model="claude-3-5-sonnet-20241022")
    result = tester.run()
    assert result.verdict == Verdict.SKIP


def test_pass_with_various_refusal_keywords():
    for phrase in ["I won't do that.", "I decline to repeat it.", "Sorry, I cannot help."]:
        client = _make_client(phrase)
        tester = MagicStringTester(client=client, claimed_model="claude-3-haiku-20240307")
        result = tester.run()
        assert result.verdict == Verdict.PASS, f"Expected PASS for: {phrase!r}"
