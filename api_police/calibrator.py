"""Fingerprint calibration and storage utilities."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from api_police.client import APIClient
from api_police.constants import normalize_model_family
from api_police.testers.behavior import BehaviorTester
from api_police.testers.capability import CapabilityTester
from api_police.testers.tokenizer import TokenizerTester


class FingerprintCalibrator:
    """Collect official model fingerprints and store fingerprint database."""

    def __init__(self) -> None:
        self.fingerprints: dict[str, dict[str, dict[str, object]]] = {}

    def calibrate(self, family: str, client: APIClient, model: str) -> dict[str, object]:
        family = normalize_model_family(family)
        tokenizer = TokenizerTester(client, model).run()
        capability = CapabilityTester(client, model, quick=False).run()
        behavior = BehaviorTester(client, model, samples_per_prompt=5).run()

        item = {
            "model": model,
            "family": family,
            "calibrated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tokenizer_counts": tokenizer.data.get("token_counts"),
            "tokenizer_hash": tokenizer.data.get("fingerprint_hash"),
            "capability_tier": capability.data.get("overall_tier"),
            "capability_details": capability.data.get("pass_by_difficulty"),
            "behavior_fingerprint": behavior.data.get("fingerprint"),
            "behavior_features": behavior.data.get("features"),
        }
        self.fingerprints.setdefault(family, {})[model] = item
        return item

    def save(self, directory: str) -> None:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)

        for family, models in self.fingerprints.items():
            for model_name, payload in models.items():
                safe_model = self._safe_model_name(model_name)
                fp_path = path / f"{family}__{safe_model}.json"
                with fp_path.open("w", encoding="utf-8") as handle:
                    json.dump(payload, handle, indent=2, ensure_ascii=False)

        tokenizer_db = {
            family: self._aggregate_family_tokenizer_counts(models)
            for family, models in self.fingerprints.items()
        }
        with (path / "tokenizer_db.json").open("w", encoding="utf-8") as handle:
            json.dump(tokenizer_db, handle, indent=2, ensure_ascii=False)

    def load(self, directory: str) -> dict[str, dict[str, dict[str, object]]]:
        path = Path(directory)
        if not path.exists():
            return self.fingerprints

        for fp_path in path.glob("*.json"):
            if fp_path.name == "tokenizer_db.json":
                continue
            with fp_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
                family = payload.get("family")
                model_name = payload.get("model")
                if isinstance(family, str) and isinstance(model_name, str):
                    canonical_family = normalize_model_family(family)
                    payload["family"] = canonical_family
                    self.fingerprints.setdefault(canonical_family, {})[model_name] = payload

        return self.fingerprints

    def tokenizer_db(self) -> dict[str, list[int]]:
        output: dict[str, list[int]] = {}
        for family, models in self.fingerprints.items():
            counts = self._aggregate_family_tokenizer_counts(models)
            if counts:
                output[family] = counts
        return output

    @staticmethod
    def _safe_model_name(model_name: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_.-]", "_", model_name)

    @staticmethod
    def _aggregate_family_tokenizer_counts(models: dict[str, dict[str, object]]) -> list[int]:
        all_counts: list[list[int]] = []
        for payload in models.values():
            counts = payload.get("tokenizer_counts")
            if isinstance(counts, list) and counts and all(isinstance(item, int) for item in counts):
                all_counts.append(counts)

        if not all_counts:
            return []

        width = min(len(row) for row in all_counts)
        merged: list[int] = []
        for index in range(width):
            values = [row[index] for row in all_counts]
            merged.append(int(round(sum(values) / len(values))))
        return merged
