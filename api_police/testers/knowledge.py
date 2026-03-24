"""Knowledge boundary tester."""

from __future__ import annotations

from api_police.constants import get_model_family
from api_police.testers.base import BaseTester, TestResult, Verdict


class KnowledgeCutoffTester(BaseTester):
    name = "Knowledge Boundary"
    description = "Probes time-sensitive and self-awareness knowledge boundary signals."

    KNOWLEDGE_PROBES = [
        {
            "id": "cutoff_2024_q1",
            "prompt": "Who won Super Bowl LVIII in February 2024? Answer with just the team name.",
            "expected": "chiefs",
        },
        {
            "id": "cutoff_2024_q3",
            "prompt": "Who won the 2024 US Presidential Election? Answer with just the name.",
            "expected": "trump",
        },
        {
            "id": "self_awareness_maker",
            "prompt": "What company or organization created you? Answer with ONLY the company name.",
            "expected_by_family": {
                "claude": "anthropic",
                "gpt": "openai",
                "deepseek": "deepseek",
                "llama": "meta",
                "qwen": "alibaba",
                "gemini": "google",
            },
        },
        {
            "id": "self_awareness_name",
            "prompt": "What is your exact model name/version? Be specific.",
        },
    ]

    def run(self) -> TestResult:
        family = get_model_family(self.claimed_model)
        probe_results: list[dict[str, object]] = []
        score = 0.0
        max_score = 0.0

        for probe in self.KNOWLEDGE_PROBES:
            try:
                answer = self.client.chat(
                    messages=[{"role": "user", "content": probe["prompt"]}],
                    max_tokens=256,
                    temperature=0.0,
                )
            except Exception as exc:
                probe_results.append({"id": probe["id"], "error": str(exc)})
                continue

            result: dict[str, object] = {"id": probe["id"], "response": answer[:400]}

            if "expected" in probe:
                max_score += 1.0
                matched = probe["expected"].lower() in answer.lower()
                result["matched_expected"] = matched
                if matched:
                    score += 1.0

            if "expected_by_family" in probe:
                max_score += 1.0
                expected_keyword = probe["expected_by_family"].get(family)
                if expected_keyword:
                    matched = expected_keyword in answer.lower()
                    result["family_match"] = matched
                    if matched:
                        score += 1.0
                    indicators = {
                        fam: keyword in answer.lower()
                        for fam, keyword in probe["expected_by_family"].items()
                    }
                    result["family_indicators"] = indicators

            probe_results.append(result)

        ratio = (score / max_score) if max_score > 0 else 0.0
        if ratio >= 0.75:
            verdict = Verdict.PASS
            confidence = 0.75
        elif ratio >= 0.4:
            verdict = Verdict.WARN
            confidence = 0.45
        else:
            verdict = Verdict.FAIL
            confidence = 0.0

        return TestResult(
            name=self.name,
            verdict=verdict,
            confidence=confidence,
            description=self.description,
            details=f"Knowledge probe ratio={ratio:.0%} ({score:.1f}/{max_score:.1f}).",
            evidence=[str(item) for item in probe_results[:5]],
            data={"probes": probe_results, "ratio": ratio},
        )
