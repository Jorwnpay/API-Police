"""Tests for CLI parser."""

from __future__ import annotations

import pytest

from api_police.cli import build_parser


def test_parser_requires_base_url():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--api-key", "sk-test", "--claimed-model", "gpt-4o"])


def test_parser_requires_api_key():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--base-url", "https://api.example.com/v1", "--claimed-model", "gpt-4o"])


def test_parser_supports_claimed_model_and_mode():
    parser = build_parser()
    args = parser.parse_args(
        [
            "--base-url",
            "https://api.example.com/v1",
            "--api-key",
            "sk-test",
            "--claimed-model",
            "gpt-4o",
            "--mode",
            "full",
            "--output",
            "report.json",
        ]
    )
    assert args.claimed_model == "gpt-4o"
    assert args.mode == "full"
    assert args.output == "report.json"


def test_parser_supports_calibration_args():
    parser = build_parser()
    args = parser.parse_args(
        [
            "--base-url",
            "https://api.example.com/v1",
            "--api-key",
            "sk-test",
            "--calibrate",
            "--model-family",
            "gpt",
            "--model-name",
            "gpt-4o",
        ]
    )
    assert args.calibrate is True
    assert args.model_family == "gpt"
    assert args.model_name == "gpt-4o"


def test_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(
        [
            "--base-url",
            "https://api.example.com/v1",
            "--api-key",
            "sk-test",
            "--claimed-model",
            "gpt-4o",
        ]
    )
    assert args.mode == "quick"
    assert args.timeout == 60.0
