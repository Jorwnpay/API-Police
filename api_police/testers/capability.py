"""Capability ladder test.

Weak models can masquerade identity but cannot consistently pass higher-tier
reasoning tasks. This layer estimates an inferred capability tier.
"""

from __future__ import annotations

from typing import Callable

from api_police.constants import CapabilityQuestion, get_model_tier
from api_police.testers.base import BaseTester, TestResult, Verdict


def _contains_last_line(expected_values: list[str]) -> Callable[[str], bool]:
    def _checker(answer: str) -> bool:
        last_line = answer.strip().split("\n")[-1].lower()
        return any(v.lower() in last_line for v in expected_values)

    return _checker


CAPABILITY_QUESTIONS: list[tuple[CapabilityQuestion, Callable[[str], bool]]] = [
    (
        CapabilityQuestion(
            id="math_basic_1",
            difficulty=1,
            prompt="What is 17 × 24? Respond with ONLY the number, nothing else.",
            expected_pass_tier=1,
        ),
        lambda r: "408" in r.strip(),
    ),
    (
        CapabilityQuestion(
            id="math_multi_step",
            difficulty=2,
            prompt=(
                "A store has 3 shelves. Each shelf has 4 boxes. Each box contains 6 red balls "
                "and 8 blue balls. How many balls are there in total? "
                "Think step by step, then answer with ONLY the final number on the last line."
            ),
            expected_pass_tier=2,
        ),
        _contains_last_line(["168"]),
    ),
    (
        CapabilityQuestion(
            id="logic_bat_ball",
            difficulty=3,
            prompt=(
                "A bat and a ball cost $1.10 in total. "
                "The bat costs $1.00 more than the ball. "
                "How much does the ball cost? "
                "Answer with ONLY the dollar amount (e.g., $X.XX)."
            ),
            expected_pass_tier=3,
        ),
        lambda r: ("0.05" in r or "5 cents" in r.lower()),
    ),
    (
        CapabilityQuestion(
            id="logic_syllogism",
            difficulty=3,
            prompt=(
                "Consider this argument:\n"
                "Premise 1: All roses are flowers.\n"
                "Premise 2: Some flowers fade quickly.\n"
                "Conclusion: Therefore, some roses fade quickly.\n\n"
                "Is this argument logically VALID? Answer ONLY 'Valid' or 'Invalid'."
            ),
            expected_pass_tier=3,
        ),
        lambda r: "invalid" in r.strip().lower(),
    ),
    (
        CapabilityQuestion(
            id="reasoning_complex",
            difficulty=4,
            prompt=(
                "In a room, there are 3 switches outside and 3 light bulbs inside. "
                "You can only enter the room once. Each switch controls exactly one bulb. "
                "How can you determine which switch controls which bulb? "
                "Describe the key insight in one sentence, then give the answer."
            ),
            expected_pass_tier=3,
        ),
        lambda r: any(k in r.lower() for k in ["heat", "warm", "touch"]),
    ),
    (
        CapabilityQuestion(
            id="code_algorithm",
            difficulty=4,
            prompt=(
                "Write a Python function that finds the longest palindromic substring "
                "in a given string. Use dynamic programming. Return ONLY the function code."
            ),
            expected_pass_tier=3,
        ),
        lambda r: "def " in r and any(k in r.lower() for k in ["dp", "table", "["]),
    ),
    (
        CapabilityQuestion(
            id="math_advanced",
            difficulty=5,
            prompt=(
                "Find the sum of all positive integers n < 1000 such that n² + n + 1 is divisible by 7. "
                "Show your reasoning, then give the final answer on the last line as 'Answer: X'."
            ),
            expected_pass_tier=5,
        ),
        lambda r: any(s in r for s in ["142571", "142,571"]),
    ),
    (
        CapabilityQuestion(
            id="instruction_precise",
            difficulty=5,
            prompt=(
                "Follow these instructions EXACTLY:\n"
                "1. Write exactly 4 sentences.\n"
                "2. Each sentence must have exactly 5 words.\n"
                "3. The first word of each sentence must start with letters A, B, C, D respectively.\n"
                "4. No sentence may contain the word 'the'.\n"
                "5. End each sentence with a period.\n"
                "Write ONLY the four sentences, nothing else."
            ),
            expected_pass_tier=4,
        ),
        lambda r: len([s for s in r.strip().split(".") if s.strip()]) == 4,
    ),
]


class CapabilityTester(BaseTester):
    name = "Capability Ladder"
    description = "Runs tiered reasoning probes and infers model capability tier."

    def __init__(self, client, claimed_model: str, quick: bool = False) -> None:
        super().__init__(client, claimed_model)
        self.quick = quick

    def run(self) -> TestResult:
        questions = CAPABILITY_QUESTIONS[:4] if self.quick else CAPABILITY_QUESTIONS
        pass_by_difficulty: dict[int, dict[str, int]] = {}
        details: list[dict[str, object]] = []

        for q, validator in questions:
            try:
                answer = self.client.chat(
                    messages=[{"role": "user", "content": q.prompt}],
                    max_tokens=1024,
                    temperature=0.0,
                )
                passed = validator(answer)
                details.append(
                    {
                        "id": q.id,
                        "difficulty": q.difficulty,
                        "passed": passed,
                        "expected_pass_tier": q.expected_pass_tier,
                        "response_preview": answer[:200],
                    }
                )
            except Exception as exc:
                passed = False
                details.append(
                    {
                        "id": q.id,
                        "difficulty": q.difficulty,
                        "passed": False,
                        "error": str(exc),
                    }
                )

            slot = pass_by_difficulty.setdefault(q.difficulty, {"passed": 0, "total": 0})
            slot["total"] += 1
            if passed:
                slot["passed"] += 1

        inferred_tier = self._infer_tier(pass_by_difficulty)
        claimed_tier = get_model_tier(self.claimed_model)

        if inferred_tier >= claimed_tier:
            verdict = Verdict.PASS
            confidence = 1.0
            details_text = f"Inferred tier {inferred_tier}, matches/exceeds claimed tier {claimed_tier}."
        elif inferred_tier >= max(1, claimed_tier - 1):
            verdict = Verdict.WARN
            confidence = 0.5
            details_text = f"Inferred tier {inferred_tier}, slightly below claimed tier {claimed_tier}."
        else:
            verdict = Verdict.FAIL
            confidence = 0.0
            details_text = f"Inferred tier {inferred_tier}, far below claimed tier {claimed_tier}."

        return TestResult(
            name=self.name,
            verdict=verdict,
            confidence=confidence,
            description=self.description,
            details=details_text,
            evidence=[str(item) for item in details[:6]],
            data={
                "pass_by_difficulty": pass_by_difficulty,
                "overall_tier": inferred_tier,
                "claimed_tier": claimed_tier,
                "details": details,
            },
        )

    @staticmethod
    def _infer_tier(pass_by_diff: dict[int, dict[str, int]]) -> int:
        tier = 0
        for diff in sorted(pass_by_diff.keys()):
            info = pass_by_diff[diff]
            total = info["total"]
            rate = (info["passed"] / total) if total > 0 else 0
            if rate >= 0.5:
                tier = diff
            else:
                break
        return tier
