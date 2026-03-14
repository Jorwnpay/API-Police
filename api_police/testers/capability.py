"""Capability fingerprinting test.

Frontier models (GPT-4, Claude 3+, Gemini Ultra, etc.) have substantially
higher reasoning accuracy than older or weaker models. This test uses a small
set of multi-step reasoning problems with known correct answers to gauge
capability level. Consistently wrong answers strongly suggest the API is
returning a weaker model than claimed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from api_police.client import APIClient
from api_police.testers.base import BaseTester, TestResult, Verdict


@dataclass
class ReasoningProbe:
    question: str
    # Callable that returns True if the reply is correct.
    # Stored as (expected_answer, check_mode) where check_mode is "exact" or "contains".
    expected: str
    check_mode: str = "contains"  # "exact" | "contains"
    difficulty: str = "medium"  # "easy" | "medium" | "hard"
    note: str = ""


PROBES: list[ReasoningProbe] = [
    ReasoningProbe(
        question=(
            "What is 17 multiplied by 13? Reply with just the number."
        ),
        expected="221",
        check_mode="contains",
        difficulty="easy",
        note="17 × 13 = 221",
    ),
    ReasoningProbe(
        question=(
            "A bat and a ball cost $1.10 in total. "
            "The bat costs $1.00 more than the ball. "
            "How much does the ball cost? Give the answer in cents (e.g. 5 cents)."
        ),
        expected="5",
        check_mode="contains",
        difficulty="medium",
        note="The ball costs 5 cents (classic cognitive reflection test).",
    ),
    ReasoningProbe(
        question=(
            "If all Bloops are Razzies, and all Razzies are Lazzies, "
            "are all Bloops definitely Lazzies? "
            "Answer with just Yes or No."
        ),
        expected="yes",
        check_mode="contains",
        difficulty="easy",
        note="Syllogism: Yes, all Bloops are Lazzies.",
    ),
    ReasoningProbe(
        question=(
            "What is the next number in the sequence: 2, 6, 12, 20, 30, ___? "
            "Reply with just the number."
        ),
        expected="42",
        check_mode="contains",
        difficulty="medium",
        note="n*(n+1) pattern: 6*7=42.",
    ),
    ReasoningProbe(
        question=(
            "Sally has 3 brothers. Each brother has 2 sisters. "
            "How many sisters does Sally have? Reply with just the number."
        ),
        expected="1",
        check_mode="contains",
        difficulty="medium",
        note=(
            "Sally has 1 sister. Each brother has 2 sisters: Sally + 1 other girl."
        ),
    ),
]


def _check_reply(reply: str, probe: ReasoningProbe) -> bool:
    reply_lower = reply.lower().strip()
    expected_lower = probe.expected.lower()
    if probe.check_mode == "exact":
        return reply_lower == expected_lower
    return expected_lower in reply_lower


class CapabilityTester(BaseTester):
    """Test reasoning capability to detect under-powered substitute models."""

    name = "Reasoning Capability Benchmark"
    description = (
        "Runs a small set of multi-step reasoning and math problems that "
        "frontier models answer correctly. Significant failure rate suggests "
        "the model is weaker than claimed."
    )

    def run(self) -> TestResult:
        passed_probes: list[str] = []
        failed_probes: list[str] = []

        for probe in PROBES:
            try:
                reply = self.client.chat(
                    messages=[{"role": "user", "content": probe.question}],
                    max_tokens=128,
                    temperature=0.0,
                )
            except Exception as exc:
                failed_probes.append(f"[API error] {probe.question[:60]}… → {exc}")
                continue

            if _check_reply(reply, probe):
                passed_probes.append(
                    f"✓ {probe.question[:60]}… | Expected: '{probe.expected}' | Got: '{reply[:80]}'"
                )
            else:
                failed_probes.append(
                    f"✗ {probe.question[:60]}… | Expected: '{probe.expected}' | Got: '{reply[:80]}'"
                )

        total = len(PROBES)
        passed_count = len(passed_probes)
        ratio = passed_count / total if total > 0 else 0.0

        if ratio >= 0.8:
            verdict = Verdict.PASS
        elif ratio >= 0.5:
            verdict = Verdict.WARN
        else:
            verdict = Verdict.FAIL

        return TestResult(
            name=self.name,
            verdict=verdict,
            confidence=ratio * 0.7,  # max 0.7 contribution
            description=self.description,
            details=f"Passed {passed_count}/{total} reasoning probes (ratio={ratio:.0%}).",
            evidence=passed_probes + [f"FAILED: {f}" for f in failed_probes],
        )
