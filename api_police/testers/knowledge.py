"""Knowledge-cutoff fingerprinting test.

Each model family has a documented training data cutoff date. This test asks
the model factual questions about events that happened *before* the claimed
model's cutoff date. If the model consistently fails to know facts it should
know, the returned model may not be the claimed one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from api_police.client import APIClient
from api_police.testers.base import BaseTester, TestResult, Verdict

# ---------------------------------------------------------------------------
# Probe database
# Each probe contains a question, the expected (correct) answer substring, and
# the model families for which the probe is valid (knowledge should exist).
# ---------------------------------------------------------------------------
@dataclass
class KnowledgeProbe:
    question: str
    expected_keywords: list[str]  # at least one must appear in the reply
    applicable_families: list[str]  # e.g. ["claude", "gpt"]
    note: str = ""


# Public, well-known facts that all current frontier models should know.
PROBES: list[KnowledgeProbe] = [
    KnowledgeProbe(
        question="Who won the FIFA World Cup in 2022? Just name the country.",
        expected_keywords=["argentina"],
        applicable_families=["claude", "gpt", "gemini", "llama", "mistral", "qwen"],
        note="Argentina won the 2022 FIFA World Cup.",
    ),
    KnowledgeProbe(
        question=(
            "What is the chemical symbol for gold? "
            "Reply with just the symbol."
        ),
        expected_keywords=["au"],
        applicable_families=["claude", "gpt", "gemini", "llama", "mistral", "qwen"],
        note="Au is the chemical symbol for gold.",
    ),
    KnowledgeProbe(
        question=(
            "Which company developed the GPT-4 language model? "
            "Reply with just the company name."
        ),
        expected_keywords=["openai", "open ai"],
        applicable_families=["claude", "gpt", "gemini", "llama", "mistral", "qwen"],
        note="OpenAI developed GPT-4.",
    ),
    KnowledgeProbe(
        question=(
            "What is the capital of France? Reply with just the city name."
        ),
        expected_keywords=["paris"],
        applicable_families=["claude", "gpt", "gemini", "llama", "mistral", "qwen"],
        note="Paris is the capital of France.",
    ),
    KnowledgeProbe(
        question=(
            "In what year did the first iPhone launch? Reply with just the year."
        ),
        expected_keywords=["2007"],
        applicable_families=["claude", "gpt", "gemini", "llama", "mistral", "qwen"],
        note="First iPhone launched in 2007.",
    ),
]


def _get_family(model_name: str) -> str:
    """Return a normalised family label from a model name."""
    name = model_name.lower()
    for family in ["claude", "gpt", "gemini", "llama", "mistral", "qwen"]:
        if family in name:
            return family
    return "unknown"


class KnowledgeCutoffTester(BaseTester):
    """Verify that the model has the expected world-knowledge for its family."""

    name = "Knowledge Cutoff / Factual Accuracy"
    description = (
        "Asks several factual questions whose answers are well within any "
        "current frontier model's training data. Significant factual failures "
        "suggest the model is weaker than claimed."
    )

    def run(self) -> TestResult:
        family = _get_family(self.claimed_model)
        applicable = [p for p in PROBES if family in p.applicable_families or family == "unknown"]

        if not applicable:
            return TestResult(
                name=self.name,
                verdict=Verdict.SKIP,
                confidence=0.0,
                description=self.description,
                details=f"No probes defined for model family '{family}'.",
            )

        passed_probes: list[str] = []
        failed_probes: list[str] = []

        for probe in applicable:
            try:
                reply = self.client.chat(
                    messages=[{"role": "user", "content": probe.question}],
                    max_tokens=64,
                    temperature=0.0,
                )
            except Exception as exc:
                failed_probes.append(f"[API error] {probe.question[:60]}… → {exc}")
                continue

            reply_lower = reply.lower()
            if any(kw in reply_lower for kw in probe.expected_keywords):
                passed_probes.append(
                    f"Q: {probe.question[:60]}… | Expected: {probe.expected_keywords} | Got: {reply[:80]}"
                )
            else:
                failed_probes.append(
                    f"Q: {probe.question[:60]}… | Expected: {probe.expected_keywords} | Got: {reply[:80]}"
                )

        total = len(applicable)
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
            confidence=ratio * 0.6,  # max 0.6 contribution from knowledge test
            description=self.description,
            details=f"Passed {passed_count}/{total} factual probes (ratio={ratio:.0%}).",
            evidence=passed_probes + [f"FAILED: {f}" for f in failed_probes],
        )
