"""API client wrapper that supports OpenAI-compatible endpoints."""

from __future__ import annotations

import time
from typing import Any

from openai import OpenAI


class APIClient:
    """Thin wrapper around the OpenAI client for calling any compatible API."""

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self._client = OpenAI(base_url=self.base_url, api_key=self.api_key, timeout=timeout)

    def create_chat_completion(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.0,
        logprobs: bool = False,
        top_logprobs: int | None = None,
        stream: bool = False,
    ) -> Any:
        """Send a chat completion request and return raw SDK response."""
        return self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            logprobs=logprobs,
            top_logprobs=top_logprobs,
            stream=stream,
        )

    def chat(self, messages: list[dict[str, str]], max_tokens: int = 512, temperature: float = 0.0) -> str:
        """Send a chat request and return the assistant's reply text."""
        response = self.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    def chat_with_usage(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 16,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """Return text and usage details for tokenizer-oriented tests."""
        response = self.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        usage = getattr(response, "usage", None)
        return {
            "text": response.choices[0].message.content or "",
            "usage": {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            },
            "raw": response,
        }

    def stream_chat_timing(
        self,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """Stream response and measure timing metrics (TTFT/TPS)."""
        start = time.perf_counter()
        first_token_time: float | None = None
        chunk_count = 0
        text_chunks: list[str] = []

        stream = self.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )

        for chunk in stream:
            if not getattr(chunk, "choices", None):
                continue
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                text_chunks.append(content)
                chunk_count += 1

        end = time.perf_counter()
        ttft = (first_token_time - start) if first_token_time else None
        generation_time = (end - first_token_time) if first_token_time else None
        tps = (chunk_count / generation_time) if generation_time and generation_time > 0 else None

        return {
            "text": "".join(text_chunks),
            "ttft": ttft,
            "total_time": end - start,
            "tps": tps,
            "chunk_count": chunk_count,
        }
