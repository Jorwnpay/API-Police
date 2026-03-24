"""Core orchestration for API Police audits and calibration."""

from __future__ import annotations

from dataclasses import dataclass

from api_police.analyzer import Analyzer
from api_police.calibrator import FingerprintCalibrator
from api_police.client import APIClient
from api_police.testers.base import TestResult
from api_police.testers.behavior import BehaviorTester
from api_police.testers.capability import CapabilityTester
from api_police.testers.direct_probe import DirectProbeTester
from api_police.testers.knowledge import KnowledgeCutoffTester
from api_police.testers.logprobs import LogProbsTester
from api_police.testers.performance import PerformanceTester
from api_police.testers.tokenizer import TokenizerTester


@dataclass
class AuditResult:
    base_url: str
    claimed_model: str
    mode: str
    test_results: list[TestResult]
    analysis: dict[str, object]


def run_audit(
    base_url: str,
    api_key: str,
    claimed_model: str,
    mode: str = "quick",
    timeout: float = 60.0,
    fingerprint_dir: str = "fingerprints",
) -> AuditResult:
    client = APIClient(base_url=base_url, api_key=api_key, model=claimed_model, timeout=timeout)

    calibrator = FingerprintCalibrator()
    calibrator.load(fingerprint_dir)
    tokenizer_db = calibrator.tokenizer_db()

    results: list[TestResult] = []

    results.append(TokenizerTester(client, claimed_model, tokenizer_db).run())

    if mode == "quick":
        results.append(CapabilityTester(client, claimed_model, quick=True).run())
        results.append(DirectProbeTester(client, claimed_model).run())
    else:
        results.append(CapabilityTester(client, claimed_model, quick=False).run())
        results.append(BehaviorTester(client, claimed_model, samples_per_prompt=3).run())
        results.append(LogProbsTester(client, claimed_model).run())
        results.append(PerformanceTester(client, claimed_model, runs_per_test=3).run())
        results.append(KnowledgeCutoffTester(client, claimed_model).run())
        results.append(DirectProbeTester(client, claimed_model).run())

    analysis = Analyzer(claimed_model).analyze(results)

    return AuditResult(
        base_url=base_url,
        claimed_model=claimed_model,
        mode=mode,
        test_results=results,
        analysis=analysis,
    )


def run_calibration(
    base_url: str,
    api_key: str,
    model_name: str,
    model_family: str,
    timeout: float = 60.0,
    fingerprint_dir: str = "fingerprints",
) -> dict[str, object]:
    client = APIClient(base_url=base_url, api_key=api_key, model=model_name, timeout=timeout)
    calibrator = FingerprintCalibrator()
    calibrator.load(fingerprint_dir)
    result = calibrator.calibrate(model_family, client, model_name)
    calibrator.save(fingerprint_dir)
    return result
