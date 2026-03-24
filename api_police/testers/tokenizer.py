"""Tokenizer fingerprint test.

Compares prompt token counts across crafted probe strings to identify model family.
"""

from __future__ import annotations

import hashlib

from api_police.constants import get_model_family
from api_police.testers.base import BaseTester, TestResult, Verdict


class TokenizerTester(BaseTester):
    name = "Tokenizer Fingerprint"
    description = "Compares prompt token-count signature against known family fingerprints."

    PROBE_STRINGS = [
        "The quick brown fox jumps over the lazy dog.",
        "antidisestablishmentarianism and pneumonoultramicroscopicsilicovolcanoconiosis",
        "人工智能是计算机科学的一个重要分支，旨在研究和开发模拟人类智能的理论和技术。",
        "Hello世界こんにちは안녕하세요مرحبا",
        "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
        "🤖🧠💡🔬🌍🚀✨🎯🔥💪👨‍👩‍👧‍👦",
        "∫₀^∞ e^(-x²) dx = √(π)/2, ∀ε>0 ∃δ>0: |x-a|<δ → |f(x)-L|<ε",
        "3.14159265358979323846264338327950288419716939937510",
        '{"users":[{"name":"Alice","age":30},{"name":"Bob","age":25}],"meta":{"total":2}}',
        "https://api.example.com/v1/chat/completions?model=gpt-4&temperature=0.7&max_tokens=4096",
        "SELECT u.name, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.name",
        "①②③④⑤ αβγδε ÀÁÂÃÄÅ ñ ü ø æ ∑∏∫∂∇",
    ]

    def __init__(self, client, claimed_model: str, known_fingerprints: dict[str, list[int]] | None = None) -> None:
        super().__init__(client, claimed_model)
        self.known_fingerprints = known_fingerprints or {}

    def run(self) -> TestResult:
        token_counts: list[int | None] = []
        probe_details: list[dict[str, object]] = []

        for idx, probe in enumerate(self.PROBE_STRINGS):
            try:
                result = self.client.chat_with_usage(
                    messages=[{"role": "user", "content": probe}],
                    max_tokens=1,
                    temperature=0.0,
                )
                usage = result["usage"]
                prompt_tokens = usage.get("prompt_tokens")
                token_counts.append(prompt_tokens)
                probe_details.append(
                    {
                        "probe_index": idx,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": usage.get("completion_tokens"),
                        "total_tokens": usage.get("total_tokens"),
                    }
                )
            except Exception as exc:
                token_counts.append(None)
                probe_details.append({"probe_index": idx, "error": str(exc)})

        valid_counts = [count for count in token_counts if count is not None]
        fingerprint_hash = None
        if valid_counts:
            text = ",".join(str(v) for v in valid_counts)
            fingerprint_hash = hashlib.sha256(text.encode()).hexdigest()[:16]

        comparison = self.compare_with_known(token_counts, self.known_fingerprints)
        claimed_family = get_model_family(self.claimed_model)

        if not self.known_fingerprints or comparison["best_match"] is None:
            verdict = Verdict.WARN
            confidence = 0.4
            details = "Fingerprint database missing or insufficient data; captured raw tokenizer signature only."
        elif comparison["best_match"] == claimed_family and comparison["is_exact_match"]:
            verdict = Verdict.PASS
            confidence = 1.0
            details = f"Exact tokenizer match with claimed family '{claimed_family}'."
        elif comparison["best_match"] == claimed_family:
            verdict = Verdict.WARN
            confidence = 0.7
            details = f"Best tokenizer match is claimed family '{claimed_family}', but not exact."
        else:
            verdict = Verdict.FAIL
            confidence = 0.0
            details = (
                f"Tokenizer best match is '{comparison['best_match']}' while claimed family is '{claimed_family}'."
            )

        return TestResult(
            name=self.name,
            verdict=verdict,
            confidence=confidence,
            description=self.description,
            details=details,
            evidence=[f"token_counts={token_counts}", f"fingerprint_hash={fingerprint_hash}"],
            data={
                "token_counts": token_counts,
                "probe_details": probe_details,
                "fingerprint_hash": fingerprint_hash,
                "comparison": comparison,
            },
        )

    @staticmethod
    def compare_with_known(
        actual_counts: list[int | None],
        known_fingerprints: dict[str, list[int]],
    ) -> dict[str, object]:
        best_match = None
        best_score = float("inf")
        all_scores: dict[str, dict[str, float]] = {}

        for family, expected_counts in known_fingerprints.items():
            diffs = []
            for actual, expected in zip(actual_counts, expected_counts):
                if actual is not None and expected is not None:
                    diffs.append(abs(actual - expected))

            if not diffs:
                continue

            avg_diff = sum(diffs) / len(diffs)
            exact_matches = sum(1 for diff in diffs if diff == 0)
            all_scores[family] = {
                "avg_diff": avg_diff,
                "max_diff": max(diffs),
                "exact_matches": float(exact_matches),
                "total_probes": float(len(diffs)),
                "match_rate": exact_matches / len(diffs),
            }
            if avg_diff < best_score:
                best_score = avg_diff
                best_match = family

        if best_score == float("inf"):
            best_score = 0.0

        return {
            "best_match": best_match,
            "best_score": best_score,
            "all_scores": all_scores,
            "is_exact_match": best_score == 0,
        }
