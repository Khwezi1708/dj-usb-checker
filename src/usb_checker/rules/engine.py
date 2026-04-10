from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from usb_checker.normalizer import NormalizedDevice


@dataclass
class RuleResult:
    hard_failures: list[str]
    warnings: list[str]


class RulesEngine:
    def __init__(self, rules_path: Path | None = None) -> None:
        if rules_path is None:
            rules_path = Path(__file__).with_name("pioneer_profiles.json")
        self.rules = json.loads(rules_path.read_text())

    def evaluate(self, device: NormalizedDevice) -> RuleResult:
        failures: list[str] = []
        warnings: list[str] = []
        hard = self.rules["hard_requirements"]
        warning_rules = self.rules["warnings"]

        filesystem = (device.filesystem or "").strip()
        if filesystem not in hard["filesystem"]:
            failures.append("Filesystem must be FAT32 for Pioneer-safe mode.")

        partition_table = (device.partition_table or "").strip()
        if partition_table not in hard["partition_table"]:
            failures.append("Partition table must be MBR.")

        if device.partition_count != int(hard["partition_count"]):
            failures.append("USB must have exactly one partition.")

        size_limit = int(warning_rules["max_recommended_size_bytes"])
        if device.total_size_bytes > size_limit:
            warnings.append("Drive size is above conservative Pioneer recommendation.")

        label = device.volume_name or ""
        if warning_rules.get("ascii_volume_label_only", False):
            if not label.isascii():
                warnings.append("Volume label should use ASCII characters only.")
        if len(label) > int(warning_rules.get("max_volume_label_length", 16)):
            warnings.append("Volume label is longer than recommended.")

        return RuleResult(hard_failures=failures, warnings=warnings)


def evaluate_device_dict(device: dict[str, Any], rules_path: Path | None = None) -> RuleResult:
    normalized = NormalizedDevice(**device)
    return RulesEngine(rules_path=rules_path).evaluate(normalized)

