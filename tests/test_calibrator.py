"""Tests for fingerprint calibration storage behavior."""

from __future__ import annotations

import json

from api_police.calibrator import FingerprintCalibrator


def test_calibrator_keeps_multiple_models_in_same_family(tmp_path):
    calibrator = FingerprintCalibrator()

    calibrator.fingerprints = {
        "gemini": {
            "google/gemini-3-flash-preview": {
                "family": "gemini",
                "model": "google/gemini-3-flash-preview",
                "tokenizer_counts": [1, 2, 3],
            },
            "google/gemini-3-pro-preview": {
                "family": "gemini",
                "model": "google/gemini-3-pro-preview",
                "tokenizer_counts": [4, 5, 6],
            },
        }
    }

    calibrator.save(str(tmp_path))

    files = sorted(path.name for path in tmp_path.glob("*.json"))
    assert "tokenizer_db.json" in files
    assert any(name.startswith("gemini__google_gemini-3-flash-preview") for name in files)
    assert any(name.startswith("gemini__google_gemini-3-pro-preview") for name in files)

    tokenizer_db = json.loads((tmp_path / "tokenizer_db.json").read_text(encoding="utf-8"))
    assert tokenizer_db["gemini"] == [2, 4, 4]


def test_load_backward_compatible_single_payload(tmp_path):
    payload = {
        "family": "google",
        "model": "google/gemini-3-pro-preview",
        "tokenizer_counts": [10, 11],
    }
    (tmp_path / "google.json").write_text(json.dumps(payload), encoding="utf-8")

    calibrator = FingerprintCalibrator()
    loaded = calibrator.load(str(tmp_path))

    assert "gemini" in loaded
    assert "google/gemini-3-pro-preview" in loaded["gemini"]
