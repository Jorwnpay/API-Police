"""Shared constants for API Police."""

from __future__ import annotations

from dataclasses import dataclass


MODEL_FAMILIES = {
    "claude": [
        "claude-3-5-sonnet",
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",
        "claude-3-5-haiku",
        "claude-4",
    ],
    "gpt": ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo", "o1", "o3", "o4-mini"],
    "deepseek": ["deepseek-chat", "deepseek-v3", "deepseek-r1"],
    "llama": ["llama-3", "llama-3.1", "llama-3.2", "llama-4"],
    "qwen": ["qwen-turbo", "qwen-plus", "qwen-max", "qwen3"],
    "gemini": ["gemini", "google/gemini", "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"],
}


MODEL_TIERS = {
    "claude-3-5-sonnet": 5,
    "claude-3-opus": 5,
    "claude-3-sonnet": 4,
    "claude-3-haiku": 3,
    "claude-3-5-haiku": 3,
    "gpt-4o": 5,
    "gpt-4-turbo": 5,
    "gpt-4": 5,
    "gpt-3.5-turbo": 2,
    "deepseek-v3": 4,
    "deepseek-r1": 5,
    "llama-3.1-405b": 4,
    "llama-3.1-70b": 3,
    "llama-3.1-8b": 2,
    "qwen-max": 4,
    "qwen3-235b": 5,
}


def get_model_family(model_name: str) -> str:
    model_lower = model_name.lower()
    for family, names in MODEL_FAMILIES.items():
        for candidate in names:
            if candidate in model_lower:
                return family
    return "unknown"


def normalize_model_family(family: str) -> str:
    canonical = family.strip().lower()
    aliases = {
        "google": "gemini",
        "openai": "gpt",
        "anthropic": "claude",
        "meta": "llama",
        "alibaba": "qwen",
    }
    return aliases.get(canonical, canonical)


def get_model_tier(model_name: str, default: int = 3) -> int:
    model_lower = model_name.lower()
    for model_key, tier in MODEL_TIERS.items():
        if model_key in model_lower:
            return tier
    return default


@dataclass
class CapabilityQuestion:
    id: str
    difficulty: int
    prompt: str
    expected_pass_tier: int
