"""Performance profiling test (TTFT and throughput)."""

from __future__ import annotations

import statistics

from api_police.testers.base import BaseTester, TestResult, Verdict


class PerformanceTester(BaseTester):
    name = "Performance Profile"
    description = "Measures TTFT and generation speed profile under streaming responses."

    PROMPTS = [
        {"prompt": "Say 'hello' and nothing else.", "max_tokens": 10},
        {"prompt": "Count from 1 to 50, each number on a new line.", "max_tokens": 300},
        {"prompt": "Summarize in one word: " + "The quick brown fox. " * 100, "max_tokens": 10},
    ]

    def __init__(self, client, claimed_model: str, runs_per_test: int = 3) -> None:
        super().__init__(client, claimed_model)
        self.runs_per_test = runs_per_test

    def run(self) -> TestResult:
        timings: list[dict[str, float]] = []
        errors: list[str] = []

        for test in self.PROMPTS:
            for _ in range(self.runs_per_test):
                try:
                    timing = self.client.stream_chat_timing(
                        messages=[{"role": "user", "content": test["prompt"]}],
                        max_tokens=test["max_tokens"],
                        temperature=0.0,
                    )
                    if timing["ttft"] is not None:
                        timings.append(
                            {
                                "ttft": float(timing["ttft"]),
                                "tps": float(timing["tps"] or 0.0),
                                "total_time": float(timing["total_time"]),
                            }
                        )
                except Exception as exc:
                    errors.append(str(exc))

        if not timings:
            return TestResult(
                name=self.name,
                verdict=Verdict.SKIP,
                confidence=0.0,
                description=self.description,
                details="No valid streaming timings captured.",
                evidence=errors[:3],
                data={"timings": [], "errors": errors},
            )

        avg_ttft = statistics.mean(item["ttft"] for item in timings)
        avg_tps = statistics.mean(item["tps"] for item in timings)
        avg_total = statistics.mean(item["total_time"] for item in timings)

        verdict = Verdict.PASS if len(timings) >= 3 else Verdict.WARN
        confidence = 0.75 if verdict == Verdict.PASS else 0.45

        return TestResult(
            name=self.name,
            verdict=verdict,
            confidence=confidence,
            description=self.description,
            details=f"avg_ttft={avg_ttft:.3f}s, avg_tps={avg_tps:.2f}, avg_total={avg_total:.3f}s.",
            evidence=[f"timing_samples={len(timings)}"] + errors[:2],
            data={
                "timings": timings,
                "avg_ttft": avg_ttft,
                "avg_tps": avg_tps,
                "avg_total": avg_total,
                "errors": errors,
            },
        )
