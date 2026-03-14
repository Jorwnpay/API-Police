"""Base class for all API verification testers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from api_police.client import APIClient


class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"


@dataclass
class TestResult:
    """Result from a single verification test."""

    name: str
    verdict: Verdict
    confidence: float  # 0.0 – 1.0 (contribution to overall authenticity score)
    description: str
    details: str = ""
    evidence: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.verdict == Verdict.PASS

    @property
    def emoji(self) -> str:
        return {
            Verdict.PASS: "✅",
            Verdict.FAIL: "❌",
            Verdict.WARN: "⚠️",
            Verdict.SKIP: "⏭️",
        }[self.verdict]


class BaseTester(ABC):
    """Abstract base class for API verification testers."""

    #: Human-readable name shown in the report.
    name: str = "BaseTester"
    #: Short description of what this test checks.
    description: str = ""

    def __init__(self, client: APIClient, claimed_model: str) -> None:
        self.client = client
        self.claimed_model = claimed_model

    @abstractmethod
    def run(self) -> TestResult:
        """Execute the test and return a result."""
