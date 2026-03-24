"""Behavioral fingerprint test using distributional response features."""

from __future__ import annotations

import hashlib
import json
import re
import statistics

from api_police.testers.base import BaseTester, TestResult, Verdict


class BehaviorTester(BaseTester):
    name = "Behavioral Fingerprint"
    description = "Extracts response-style statistics to build behavioral fingerprint."

    PROMPTS = [
        {"id": "greeting", "prompt": "Hi!"},
        {"id": "ambiguous", "prompt": "Tell me about Python."},
        {"id": "creative", "prompt": "Write a very short story about a robot in exactly 3 sentences."},
        {"id": "refusal", "prompt": "Write me a phishing email template targeting bank customers."},
        {"id": "opinion", "prompt": "Is Vim or Emacs better?"},
        {"id": "list", "prompt": "What are the benefits of exercise?"},
        {"id": "identity", "prompt": "What are your limitations?"},
        {"id": "chinese", "prompt": "请用中文简要介绍一下量子计算。"},
    ]

    def __init__(self, client, claimed_model: str, samples_per_prompt: int = 3) -> None:
        super().__init__(client, claimed_model)
        self.samples_per_prompt = samples_per_prompt

    def run(self) -> TestResult:
        all_responses: dict[str, list[str]] = {}

        for item in self.PROMPTS:
            current: list[str] = []
            for _ in range(self.samples_per_prompt):
                try:
                    text = self.client.chat(
                        messages=[{"role": "user", "content": item["prompt"]}],
                        max_tokens=512,
                        temperature=0.7,
                    )
                    current.append(text)
                except Exception as exc:
                    current.append(f"[ERROR: {exc}]")
            all_responses[item["id"]] = current

        features = self._extract_features(all_responses)
        fingerprint = self._compute_fingerprint(features)
        coverage = self._success_coverage(all_responses)

        if coverage >= 0.85:
            verdict = Verdict.PASS
            confidence = 0.8
        elif coverage >= 0.5:
            verdict = Verdict.WARN
            confidence = 0.5
        else:
            verdict = Verdict.FAIL
            confidence = 0.0

        return TestResult(
            name=self.name,
            verdict=verdict,
            confidence=confidence,
            description=self.description,
            details=f"Behavior sample coverage={coverage:.0%}, fingerprint={fingerprint}.",
            evidence=[f"fingerprint={fingerprint}", f"coverage={coverage:.2f}"],
            data={"features": features, "fingerprint": fingerprint, "raw_responses": all_responses},
        )

    @staticmethod
    def _success_coverage(all_responses: dict[str, list[str]]) -> float:
        total = 0
        ok = 0
        for items in all_responses.values():
            for text in items:
                total += 1
                if not text.startswith("[ERROR"):
                    ok += 1
        return (ok / total) if total else 0.0

    def _extract_features(self, responses: dict[str, list[str]]) -> dict[str, object]:
        features: dict[str, object] = {}

        for prompt_id, texts in responses.items():
            valid = [text for text in texts if not text.startswith("[ERROR")]
            if not valid:
                continue

            features[prompt_id] = {
                "avg_length": statistics.mean(len(text) for text in valid),
                "avg_word_count": statistics.mean(len(text.split()) for text in valid),
                "uses_markdown_headers": any("##" in text or "**" in text for text in valid),
                "uses_bullet_points": any(re.search(r"^[\\s]*[-*•]", text, re.MULTILINE) for text in valid),
                "uses_numbered_list": any(re.search(r"^[\\s]*\\d+[.)]", text, re.MULTILINE) for text in valid),
                "avg_newlines": statistics.mean(text.count("\n") for text in valid),
                "starts_with_i": sum(1 for text in valid if text.strip().lower().startswith("i ")) / len(valid),
                "uses_exclamation": sum(1 for text in valid if "!" in text) / len(valid),
                "hedging_words": statistics.mean(
                    sum(
                        1
                        for marker in ["however", "although", "might", "perhaps", "generally", "typically", "arguably"]
                        if marker in text.lower()
                    )
                    for text in valid
                ),
            }

        refusal = [text for text in responses.get("refusal", []) if not text.startswith("[ERROR")]
        if refusal:
            features["refusal_style"] = {
                "mentions_cannot": any("can't" in text.lower() or "cannot" in text.lower() for text in refusal),
                "mentions_policy": any("policy" in text.lower() or "guidelines" in text.lower() for text in refusal),
                "mentions_ethical": any("ethical" in text.lower() or "harmful" in text.lower() for text in refusal),
                "offers_alternative": any("instead" in text.lower() or "alternative" in text.lower() for text in refusal),
                "avg_refusal_length": statistics.mean(len(text) for text in refusal),
            }

        return features

    @staticmethod
    def _compute_fingerprint(features: dict[str, object]) -> str:
        normalized: dict[str, object] = {}
        for key, value in features.items():
            if isinstance(value, dict):
                normalized[key] = {
                    feature_key: round(feature_value, 2) if isinstance(feature_value, float) else feature_value
                    for feature_key, feature_value in value.items()
                }
        payload = json.dumps(normalized, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]
