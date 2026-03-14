"""Tests for the APIClient wrapper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from api_police.client import APIClient


@pytest.fixture()
def mock_openai(monkeypatch):
    """Patch the OpenAI constructor and return the mock client."""
    with patch("api_police.client.OpenAI") as MockOpenAI:
        mock_instance = MagicMock()
        MockOpenAI.return_value = mock_instance
        yield mock_instance


def _make_response(content: str):
    """Build a minimal mock completion response."""
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


def test_client_init(mock_openai):
    client = APIClient(
        base_url="https://api.example.com/v1",
        api_key="sk-test",
        model="gpt-4o",
    )
    assert client.model == "gpt-4o"
    assert client.base_url == "https://api.example.com/v1"


def test_client_strips_trailing_slash(mock_openai):
    client = APIClient(
        base_url="https://api.example.com/v1/",
        api_key="sk-test",
        model="gpt-4o",
    )
    assert client.base_url == "https://api.example.com/v1"


def test_chat_returns_content(mock_openai):
    mock_openai.chat.completions.create.return_value = _make_response("Hello!")
    client = APIClient(base_url="https://api.example.com/v1", api_key="sk-test", model="gpt-4o")
    result = client.chat(messages=[{"role": "user", "content": "Hi"}])
    assert result == "Hello!"


def test_chat_handles_none_content(mock_openai):
    mock_openai.chat.completions.create.return_value = _make_response(None)
    client = APIClient(base_url="https://api.example.com/v1", api_key="sk-test", model="gpt-4o")
    result = client.chat(messages=[{"role": "user", "content": "Hi"}])
    assert result == ""
