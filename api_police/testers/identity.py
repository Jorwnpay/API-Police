"""Model identity test.

Directly asks the model to identify itself and compares the response with the
claimed model name. Note that any system prompt can override this, so a
positive result is only weak evidence; a *strongly contradictory* result is
more meaningful evidence of substitution.
"""

from __future__ import annotations

import re

from api_police.client import APIClient
from api_police.testers.base import BaseTester, TestResult, Verdict

# Common model family keywords used for fuzzy matching.
_FAMILY_KEYWORDS: dict[str, list[str]] = {
    "claude": ["claude", "anthropic"],
    "gpt": ["gpt", "openai", "chatgpt"],
    "gemini": ["gemini", "google", "bard"],
    "llama": ["llama", "meta"],
    "mistral": ["mistral"],
    "qwen": ["qwen", "alibaba", "tongyi"],
    "deepseek": ["deepseek"],
    "yi": ["yi", "01.ai"],
}

_IDENTITY_PROMPT_EN = (
    "Please tell me your exact model name and the company that created you. "
    "Be as specific as possible (e.g. 'I am Claude 3.5 Sonnet, created by Anthropic')."
)

_IDENTITY_PROMPT_ZH = (
    "请告诉我你的确切模型名称和创建你的公司。"
    "请尽可能具体（例如：'我是 Claude 3.5 Sonnet，由 Anthropic 创建'）。"
)

# Combine both English and Chinese prompts for better compatibility
_IDENTITY_PROMPT = f"{_IDENTITY_PROMPT_EN}\n\n{_IDENTITY_PROMPT_ZH}"

_EVASION_PHRASES = [
    # English phrases
    "i'm an ai",
    "i am an ai",
    "i don't have",
    "i do not have",
    "cannot disclose",
    "not able to tell",
    "not allowed",
    "confidential",
    "i'm just an assistant",
    # Chinese phrases
    "我是一个ai",
    "我是一个人工智能",
    "我没有",
    "无法透露",
    "不能告诉",
    "不允许",
    "保密",
    "我只是一个助手",
]


def _extract_family(model_name: str) -> str | None:
    name = model_name.lower()
    for family, keywords in _FAMILY_KEYWORDS.items():
        if any(kw in name for kw in keywords):
            return family
    return None


class IdentityTester(BaseTester):
    """Ask the model to identify itself and check for consistency."""

    name = "Model Self-Identification"
    description = (
        "Asks the model to state its name and creator. Checks whether the "
        "self-reported identity is consistent with the claimed model."
    )

    def run(self) -> TestResult:
        try:
            reply = self.client.chat(
                messages=[{"role": "user", "content": _IDENTITY_PROMPT}],
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

        # Check if the model is evading the question.
        is_evasive = any(phrase in reply_lower for phrase in _EVASION_PHRASES)
        if is_evasive:
            return TestResult(
                name=self.name,
                verdict=Verdict.WARN,
                confidence=0.3,
                description=self.description,
                details=(
                    "The model did not provide a clear identity. "
                    "This may be intentional (system-prompt restriction) or indicate substitution."
                ),
                evidence=[f"Model reply: {reply[:400]}"],
            )

        claimed_family = _extract_family(self.claimed_model)
        if claimed_family is None:
            # Unknown family – check for any known family in the reply.
            found_families = [
                fam
                for fam, keywords in _FAMILY_KEYWORDS.items()
                if any(kw in reply_lower for kw in keywords)
            ]
            if found_families:
                return TestResult(
                    name=self.name,
                    verdict=Verdict.WARN,
                    confidence=0.4,
                    description=self.description,
                    details=(
                        f"Claimed model family is unknown; model self-identifies as: "
                        f"{', '.join(found_families)}. Manual verification recommended."
                    ),
                    evidence=[f"Model reply: {reply[:400]}"],
                )
            return TestResult(
                name=self.name,
                verdict=Verdict.WARN,
                confidence=0.3,
                description=self.description,
                details="Could not determine claimed model family or self-reported identity.",
                evidence=[f"Model reply: {reply[:400]}"],
            )

        claimed_keywords = _FAMILY_KEYWORDS[claimed_family]
        identity_matches = any(kw in reply_lower for kw in claimed_keywords)

        # Check for clear contradictions – model claims to be a *different* family.
        other_families_found = [
            fam
            for fam, keywords in _FAMILY_KEYWORDS.items()
            if fam != claimed_family and any(kw in reply_lower for kw in keywords)
        ]

        if identity_matches and not other_families_found:
            return TestResult(
                name=self.name,
                verdict=Verdict.PASS,
                confidence=0.5,
                description=self.description,
                details=(
                    f"Model self-identifies as a '{claimed_family}' model, "
                    "consistent with the claimed model."
                ),
                evidence=[f"Model reply: {reply[:400]}"],
            )
        elif other_families_found:
            return TestResult(
                name=self.name,
                verdict=Verdict.FAIL,
                confidence=0.0,
                description=self.description,
                details=(
                    f"Model self-identifies as: {', '.join(other_families_found)} "
                    f"but claimed model is '{self.claimed_model}'. "
                    "This is a strong indicator of model substitution."
                ),
                evidence=[f"Model reply: {reply[:400]}"],
            )
        else:
            return TestResult(
                name=self.name,
                verdict=Verdict.WARN,
                confidence=0.2,
                description=self.description,
                details=(
                    f"Could not confirm the model is a '{claimed_family}' model "
                    "from its self-description."
                ),
                evidence=[f"Model reply: {reply[:400]}"],
            )
