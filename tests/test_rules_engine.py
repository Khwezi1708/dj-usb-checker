from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str((Path(__file__).resolve().parents[1] / "src")))

from usb_checker.rules.engine import evaluate_device_dict
from usb_checker.scoring import score_result
from usb_checker.health import HealthResult


FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_fat32_passes_rules() -> None:
    result = evaluate_device_dict(_fixture("fat32_good.json"))
    assert result.hard_failures == []


def test_exfat_fails_rules() -> None:
    result = evaluate_device_dict(_fixture("exfat_bad.json"))
    assert any("FAT32" in msg for msg in result.hard_failures)


def test_multi_partition_fails_rules() -> None:
    result = evaluate_device_dict(_fixture("multipartition_bad.json"))
    assert any("one partition" in msg for msg in result.hard_failures)


def test_fail_status_from_hard_failure() -> None:
    rule_result = evaluate_device_dict(_fixture("exfat_bad.json"))
    health = HealthResult(warnings=[], info=["Mount point is accessible."])
    outcome = score_result(rule_result, health)
    assert outcome.status == "FAIL"

