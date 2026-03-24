"""Tests for APIClient wrapper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from api_police.client import APIClient


@pytest.fixture()
def mock_openai():
    with patch("api_police.client.OpenAI") as mock_ctor:
        instance = MagicMock()
        mock_ctor.return_value = instance
        yield instance


def _make_response(content: str, prompt_tokens: int = 10):
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    usage = MagicMock()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = 1
    usage.total_tokens = prompt_tokens + 1
    response.usage = usage
    return response


def test_chat_returns_content(mock_openai):
    mock_openai.chat.completions.create.return_value = _make_response("Hello")
    client = APIClient(base_url="https://api.example.com/v1", api_key="sk-test", model="gpt-4o")
    assert client.chat([{"role": "user", "content": "Hi"}]) == "Hello"


def test_chat_with_usage_extracts_tokens(mock_openai):
    mock_openai.chat.completions.create.return_value = _make_response("x", prompt_tokens=42)
    client = APIClient(base_url="https://api.example.com/v1", api_key="sk-test", model="gpt-4o")
    result = client.chat_with_usage([{"role": "user", "content": "Hi"}], max_tokens=1)
    assert result["usage"]["prompt_tokens"] == 42


def test_stream_chat_timing(mock_openai):
    chunk1 = MagicMock()
    chunk1.choices = [MagicMock(delta=MagicMock(content="Hello"))]
    chunk2 = MagicMock()
    chunk2.choices = [MagicMock(delta=MagicMock(content=" world"))]
    mock_openai.chat.completions.create.return_value = [chunk1, chunk2]

    client = APIClient(base_url="https://api.example.com/v1", api_key="sk-test", model="gpt-4o")
    timing = client.stream_chat_timing([{"role": "user", "content": "Hi"}], max_tokens=8)

    assert timing["chunk_count"] == 2
    assert "Hello" in timing["text"]
