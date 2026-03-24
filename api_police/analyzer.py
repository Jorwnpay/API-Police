"""Cross-layer analyzer for final verdict generation."""

from __future__ import annotations

from api_police.constants import get_model_family
from api_police.testers.base import TestResult


class Analyzer:
    """Aggregate layer results into weighted confidence and verdict."""

    WEIGHTS = {
        "Tokenizer Fingerprint": 0.25,
        "Capability Ladder": 0.30,
        "LogProbs Distribution": 0.10,
        "Behavioral Fingerprint": 0.10,
        "Performance Profile": 0.05,
        "Knowledge Boundary": 0.10,
        "Direct Probes": 0.10,
    }

    def __init__(self, claimed_model: str) -> None:
        self.claimed_model = claimed_model
        self.claimed_family = get_model_family(claimed_model)

    def analyze(self, results: list[TestResult]) -> dict[str, object]:
        dimension_scores: dict[str, float] = {}
        flags: list[str] = []

        weighted_sum = 0.0
        weight_total = 0.0

        for result in results:
            weight = self.WEIGHTS.get(result.name, 0.05)
            score = self._normalize_score(result)
            dimension_scores[result.name] = score

            weighted_sum += score * weight
            weight_total += weight

            if result.name == "Tokenizer Fingerprint":
                comparison = result.data.get("comparison", {}) if isinstance(result.data, dict) else {}
                best_match = comparison.get("best_match")
                if best_match and best_match != self.claimed_family:
                    flags.append(
                        f"⚠️ Tokenizer 指纹更接近 [{best_match}]，而非声称的 [{self.claimed_family}]"
                    )

            if result.name == "Capability Ladder":
                claimed_tier = result.data.get("claimed_tier") if isinstance(result.data, dict) else None
                actual_tier = result.data.get("overall_tier") if isinstance(result.data, dict) else None
                if isinstance(claimed_tier, int) and isinstance(actual_tier, int) and actual_tier < claimed_tier - 1:
                    flags.append(
                        f"⚠️ 能力层级 [Tier {actual_tier}] 显著低于声称模型 [Tier {claimed_tier}]"
                    )

            if result.name == "Direct Probes":
                payload = result.data if isinstance(result.data, dict) else {}
                system_data = payload.get("system_prompt_extraction", [])
                if any(item.get("appears_to_have_disguise_prompt") for item in system_data if isinstance(item, dict)):
                    flags.append("🚨 检测到疑似伪装 system prompt")

        weighted_score = (weighted_sum / weight_total) if weight_total > 0 else 0.5
        if weighted_score >= 0.8 and not any("🚨" in flag for flag in flags):
            verdict = "✅ GENUINE (可信)"
        elif weighted_score >= 0.5:
            verdict = "⚠️ SUSPICIOUS (可疑)"
        else:
            verdict = "❌ LIKELY FAKE (很可能是假的)"

        return {
            "verdict": verdict,
            "confidence": round(weighted_score * 100, 1),
            "claimed_model": self.claimed_model,
            "claimed_family": self.claimed_family,
            "dimension_scores": dimension_scores,
            "flags": flags,
            "recommendation": self._recommendation(verdict, flags),
        }

    @staticmethod
    def _normalize_score(result: TestResult) -> float:
        if result.verdict.value == "PASS":
            return max(0.8, result.confidence)
        if result.verdict.value == "WARN":
            return min(max(result.confidence, 0.4), 0.7)
        if result.verdict.value == "FAIL":
            return min(result.confidence, 0.2)
        return 0.5

    @staticmethod
    def _recommendation(verdict: str, flags: list[str]) -> str:
        if "GENUINE" in verdict:
            return "该 API 的核心检测维度与声称模型基本一致，可继续使用并保持周期复检。"
        if "SUSPICIOUS" in verdict:
            return (
                "存在可疑迹象，建议扩大样本并对比官方 API。\n"
                "1. 增加测试轮次并随机化提示词\n"
                "2. 与官方模型做 A/B 对照\n"
                "3. 要求服务商解释异常项\n"
                + ("异常项:\n" + "\n".join(f"  {flag}" for flag in flags) if flags else "")
            )
        return (
            "多维度指标明显不匹配，建议暂停使用并保留证据。\n"
            "1. 立即停止关键业务流量\n"
            "2. 索取解释和补偿\n"
            "3. 对外公开检测证据\n"
            + ("关键证据:\n" + "\n".join(f"  {flag}" for flag in flags) if flags else "")
        )
