from __future__ import annotations

from dataclasses import dataclass

from usb_checker.health import HealthResult
from usb_checker.rules.engine import RuleResult


@dataclass
class CheckOutcome:
    status: str
    score: int
    reasons: list[str]
    warnings: list[str]
    info: list[str]


def score_result(rule_result: RuleResult, health_result: HealthResult) -> CheckOutcome:
    reasons = list(rule_result.hard_failures)
    warnings = list(rule_result.warnings) + list(health_result.warnings)
    info = list(health_result.info)

    if reasons:
        return CheckOutcome(
            status="FAIL",
            score=max(0, 30 - (len(reasons) * 10)),
            reasons=reasons,
            warnings=warnings,
            info=info,
        )

    if warnings:
        return CheckOutcome(
            status="WARN",
            score=max(70, 90 - (len(warnings) * 5)),
            reasons=[],
            warnings=warnings,
            info=info,
        )

    return CheckOutcome(status="PASS", score=100, reasons=[], warnings=[], info=info)

