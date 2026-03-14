"""Tests for the IdentityTester."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from api_police.testers.base import Verdict
from api_police.testers.identity import IdentityTester


def _make_client(reply: str) -> MagicMock:
    client = MagicMock()
    client.chat.return_value = reply
    return client


def test_pass_identity_matches_claimed():
    client = _make_client(
        "I am Claude 3.5 Sonnet, created by Anthropic."
    )
    tester = IdentityTester(client=client, claimed_model="claude-3-5-sonnet-20241022")
    result = tester.run()
    assert result.verdict == Verdict.PASS
    assert result.confidence > 0


def test_fail_identity_contradicts_claimed():
    client = _make_client(
        "I am GPT-4o, created by OpenAI."
    )
    tester = IdentityTester(client=client, claimed_model="claude-3-5-sonnet-20241022")
    result = tester.run()
    assert result.verdict == Verdict.FAIL
    assert result.confidence == 0.0


def test_warn_evasive_response():
    client = _make_client(
        "I'm an AI assistant. I don't have information about my underlying model."
    )
    tester = IdentityTester(client=client, claimed_model="gpt-4o")
    result = tester.run()
    assert result.verdict == Verdict.WARN


def test_skip_on_api_error():
    client = MagicMock()
    client.chat.side_effect = Exception("Timeout")
    tester = IdentityTester(client=client, claimed_model="gpt-4o")
    result = tester.run()
    assert result.verdict == Verdict.SKIP


def test_warn_unknown_family():
    client = _make_client("I am an advanced language model.")
    tester = IdentityTester(client=client, claimed_model="some-unknown-model-xyz")
    result = tester.run()
    assert result.verdict == Verdict.WARN


def test_fail_when_different_known_family_detected():
    """If claimed GPT but model says it's Gemini, should FAIL."""
    client = _make_client("I am Gemini Ultra, built by Google.")
    tester = IdentityTester(client=client, claimed_model="gpt-4o")
    result = tester.run()
    assert result.verdict == Verdict.FAIL
