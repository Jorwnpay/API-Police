"""API client wrapper that supports OpenAI-compatible endpoints."""

from __future__ import annotations

from openai import OpenAI


class APIClient:
    """Thin wrapper around the OpenAI client for calling any compatible API."""

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self._client = OpenAI(base_url=self.base_url, api_key=self.api_key, timeout=timeout)

    def chat(self, messages: list[dict], max_tokens: int = 512, temperature: float = 0.0) -> str:
        """Send a chat request and return the assistant's reply text."""
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""
