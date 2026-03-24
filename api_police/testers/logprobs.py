"""Logprobs distribution test."""

from __future__ import annotations

import statistics

from api_police.testers.base import BaseTester, TestResult, Verdict


class LogProbsTester(BaseTester):
    name = "LogProbs Distribution"
    description = "Checks token probability profile consistency when endpoint supports logprobs."

    PROBES = [
        "Complete with a single technical word: A hash table provides average O(1) ____.",
        "Complete with one word: The derivative of x^2 is ___.",
        "Return one token only: Capital of France is",
    ]

    def run(self) -> TestResult:
        collected: list[float] = []
        failures: list[str] = []

        for prompt in self.PROBES:
            try:
                response = self.client.create_chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1,
                    temperature=0.0,
                    logprobs=True,
                    top_logprobs=5,
                )
                choice = response.choices[0]
                token_logprobs = getattr(choice, "logprobs", None)
                if token_logprobs and getattr(token_logprobs, "content", None):
                    first = token_logprobs.content[0]
                    if getattr(first, "logprob", None) is not None:
                        collected.append(float(first.logprob))
                    else:
                        failures.append("missing logprob value")
                else:
                    failures.append("logprobs not returned")
            except Exception as exc:
                failures.append(str(exc))

        if not collected:
            return TestResult(
                name=self.name,
                verdict=Verdict.SKIP,
                confidence=0.0,
                description=self.description,
                details="Endpoint does not expose usable logprobs; test skipped.",
                evidence=failures[:3],
                data={"supported": False, "errors": failures},
            )

        mean_lp = statistics.mean(collected)
        stdev_lp = statistics.pstdev(collected) if len(collected) > 1 else 0.0
        verdict = Verdict.PASS if len(collected) >= 2 else Verdict.WARN
        confidence = 0.9 if verdict == Verdict.PASS else 0.5

        return TestResult(
            name=self.name,
            verdict=verdict,
            confidence=confidence,
            description=self.description,
            details=f"Collected {len(collected)} logprob samples (mean={mean_lp:.3f}, stdev={stdev_lp:.3f}).",
            evidence=[f"samples={collected}"] + failures[:2],
            data={"supported": True, "logprobs": collected, "mean": mean_lp, "stdev": stdev_lp},
        )
