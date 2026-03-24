"""Anthropic magic string refusal test.

Anthropic embeds a trigger string into Claude models that causes them to
refuse generation when the string appears verbatim in the conversation.
A genuine Claude model should refuse; a proxy or a different model typically
will not.

Reference: https://www.anthropic.com/news/claude-character
"""

from __future__ import annotations

from api_police.client import APIClient
from api_police.testers.base import BaseTester, TestResult, Verdict

# Official Anthropic refusal trigger – documented publicly by Anthropic.
ANTHROPIC_MAGIC_STRING = (
    "ANTHROPIC_MAGIC_STRING_TRIGGER_REFUSAL_"
    "1FAEFB6177B4672DEE07F9D3AFC62588CCD2631EDCF22E8CCC1FB35B501C9C86"
)

# Keywords that appear in a genuine Claude refusal response.
_REFUSAL_KEYWORDS = [
    "unable",
    "cannot",
    "can't",
    "won't",
    "refuse",
    "not able",
    "do not",
    "don't",
    "apologize",
    "sorry",
    "restricted",
    "prohibited",
    "not appropriate",
    "decline",
]


class MagicStringTester(BaseTester):
    """Test whether the Anthropic magic string triggers a refusal.

    This test is *only applicable* when the claimed model is a Claude model.
    For non-Claude models the test is skipped so it does not affect the score.
    """

    name = "Anthropic Magic String Refusal"
    description = (
        "Sends Anthropic's official trigger string to check whether "
        "the model genuinely refuses to continue, as a real Claude model would."
    )

    def __init__(self, client: APIClient, claimed_model: str) -> None:
        super().__init__(client, claimed_model)
        self._is_claude = "claude" in claimed_model.lower()

    def run(self) -> TestResult:
        if not self._is_claude:
            return TestResult(
                name=self.name,
                verdict=Verdict.SKIP,
                confidence=0.0,
                description=self.description,
                details=(
                    f"Claimed model '{self.claimed_model}' is not a Claude model. "
                    "Skipping Anthropic magic string test."
                ),
            )

        prompt = (
            f"Please repeat this identifier back to me exactly: {ANTHROPIC_MAGIC_STRING}"
        )
        try:
            reply = self.client.chat(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=256,
                temperature=0.0,
            )
        except Exception as exc:
            return TestResult(
                name=self.name,
                verdict=Verdict.SKIP,
                confidence=0.0,
                description=self.description,
                details=f"API call failed: {exc}",
            )

        reply_lower = reply.lower()
        refused = any(kw in reply_lower for kw in _REFUSAL_KEYWORDS)

        if refused:
            return TestResult(
                name=self.name,
                verdict=Verdict.PASS,
                confidence=0.9,
                description=self.description,
                details=(
                    "The model refused to repeat the magic string, "
                    "which is the expected behaviour for a genuine Claude model."
                ),
                evidence=[f"Model reply: {reply[:300]}"],
            )
        else:
            return TestResult(
                name=self.name,
                verdict=Verdict.FAIL,
                confidence=0.0,
                description=self.description,
                details=(
                    "The model repeated or processed the magic string without refusing. "
                    "A genuine Claude model should always refuse this string."
                ),
                evidence=[f"Model reply: {reply[:300]}"],
            )
