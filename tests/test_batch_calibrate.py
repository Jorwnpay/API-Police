"""Tests for batch calibration utility."""

from __future__ import annotations

from types import SimpleNamespace

from api_police.batch_calibrate import _build_targets, _families_from_arg


def _args(**overrides):
    data = {
        "provider": "openrouter",
        "families": "claude,gpt,gemini",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": "sk-test",
        "claude_base_url": None,
        "gpt_base_url": None,
        "gemini_base_url": None,
        "claude_api_key": None,
        "gpt_api_key": None,
        "gemini_api_key": None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_families_arg_normalization():
    assert _families_from_arg("claude,gpt,google") == ["claude", "gpt", "gemini"]


def test_build_targets_openrouter_default_count():
    args = _args()
    targets = _build_targets(args)
    assert len(targets) == 9
    assert all(target.base_url == "https://openrouter.ai/api/v1" for target in targets)


def test_build_targets_respects_family_filter():
    args = _args(families="gemini")
    targets = _build_targets(args)
    assert len(targets) == 3
    assert all(target.family == "gemini" for target in targets)
