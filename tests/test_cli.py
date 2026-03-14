"""Tests for the CLI argument parser."""

from __future__ import annotations

import pytest

from api_police.cli import build_parser


def test_parser_requires_base_url():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--api-key", "sk-test", "--model", "gpt-4o"])


def test_parser_requires_api_key():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--base-url", "https://api.example.com/v1", "--model", "gpt-4o"])


def test_parser_requires_model():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--base-url", "https://api.example.com/v1", "--api-key", "sk-test"])


def test_parser_all_args():
    parser = build_parser()
    args = parser.parse_args(
        [
            "--base-url", "https://api.example.com/v1",
            "--api-key", "sk-test",
            "--model", "gpt-4o",
            "--timeout", "30.0",
            "--verbose",
        ]
    )
    assert args.base_url == "https://api.example.com/v1"
    assert args.api_key == "sk-test"
    assert args.model == "gpt-4o"
    assert args.timeout == 30.0
    assert args.verbose is True


def test_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(
        [
            "--base-url", "https://api.example.com/v1",
            "--api-key", "sk-test",
            "--model", "gpt-4o",
        ]
    )
    assert args.timeout == 60.0
    assert args.verbose is False
