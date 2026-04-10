from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from typing import Any

from usb_checker.collector import DiskutilCollector
from usb_checker.health import quick_health_check
from usb_checker.normalizer import extract_disk_partition_count, normalize_disk
from usb_checker.rules.engine import RulesEngine
from usb_checker.scoring import CheckOutcome, score_result


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2), flush=True)


def list_external_disks(collector: DiskutilCollector) -> list[dict[str, Any]]:
    disks = collector.list_disks()
    part_counts = extract_disk_partition_count(disks)
    partitions_by_disk: dict[str, list[dict[str, Any]]] = {}
    for disk in disks.get("AllDisksAndPartitions", []):
        disk_id = str(disk.get("DeviceIdentifier", ""))
        partitions_by_disk[disk_id] = list(disk.get("Partitions") or [])

    results: list[dict[str, Any]] = []
    for disk_id in disks.get("WholeDisks", []):
        try:
            info = collector.info(str(disk_id))
        except RuntimeError:
            continue
        if not info.get("Internal", True):
            normalized = normalize_disk(info, partition_count=part_counts.get(str(disk_id), 0))
            device = normalized.to_dict()

            # Whole-disk info often lacks filesystem and mount data on macOS.
            # Pull those fields from the first partition when available.
            partition_entries = partitions_by_disk.get(str(disk_id), [])
            if partition_entries:
                first_partition_id = partition_entries[0].get("DeviceIdentifier")
                if first_partition_id:
                    try:
                        partition_info = collector.info(str(first_partition_id))
                    except RuntimeError:
                        partition_info = {}

                    if not device.get("filesystem"):
                        device["filesystem"] = partition_info.get("FilesystemName")
                    if not device.get("mount_point"):
                        device["mount_point"] = partition_info.get("MountPoint")
                    if not device.get("volume_name"):
                        device["volume_name"] = partition_info.get("VolumeName")
                    device["writable"] = bool(partition_info.get("WritableVolume", device["writable"]))

            # Fall back to disk content when partition scheme key is absent.
            if not device.get("partition_table"):
                device["partition_table"] = info.get("PartitionMapPartitionScheme") or info.get("Content")

            results.append(device)
    return results


def evaluate(normalized_device: dict[str, Any], enable_write_probe: bool = False) -> dict[str, Any]:
    from usb_checker.normalizer import NormalizedDevice

    device = NormalizedDevice(**normalized_device)
    rule_result = RulesEngine().evaluate(device)
    health_result = quick_health_check(device, enable_write_probe=enable_write_probe)
    outcome: CheckOutcome = score_result(rule_result, health_result)
    payload = {
        "device": normalized_device,
        "result": asdict(outcome),
    }
    return payload


def cmd_scan(args: argparse.Namespace) -> int:
    collector = DiskutilCollector()
    try:
        devices = list_external_disks(collector)
    except RuntimeError as exc:
        _print_json({"error": str(exc)})
        return 1
    _print_json({"devices": devices})
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    collector = DiskutilCollector()
    devices = list_external_disks(collector)
    selected = None
    for device in devices:
        if device["device_id"] == args.device:
            selected = device
            break
    if selected is None:
        _print_json({"error": f"Device {args.device} not found"})
        return 1
    _print_json(evaluate(selected, enable_write_probe=args.write_probe))
    return 0


def _snapshot_ids(devices: list[dict[str, Any]]) -> set[str]:
    return {d["device_id"] for d in devices}


def cmd_watch(args: argparse.Namespace) -> int:
    collector = DiskutilCollector()
    seen: set[str] = set()
    last_checked: dict[str, float] = {}
    debounce = float(args.debounce_sec)
    interval = float(args.poll_interval_sec)

    while True:
        try:
            devices = list_external_disks(collector)
        except RuntimeError as exc:
            _print_json({"watch_error": str(exc)})
            time.sleep(interval)
            continue
        current_ids = _snapshot_ids(devices)
        inserted = current_ids - seen
        now = time.time()

        for dev in devices:
            dev_id = dev["device_id"]
            if dev_id not in inserted:
                continue
            last_time = last_checked.get(dev_id, 0.0)
            if now - last_time < debounce:
                continue
            time.sleep(debounce)
            _print_json(evaluate(dev, enable_write_probe=args.write_probe))
            last_checked[dev_id] = time.time()

        seen = current_ids
        time.sleep(interval)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="usb-checker")
    sub = parser.add_subparsers(required=True)

    scan = sub.add_parser("scan", help="List external disks.")
    scan.set_defaults(func=cmd_scan)

    check = sub.add_parser("check", help="Check a specific disk.")
    check.add_argument("device", help="Device identifier (example: disk4)")
    check.add_argument("--write-probe", action="store_true", help="Enable small write/read probe.")
    check.set_defaults(func=cmd_check)

    watch = sub.add_parser("watch", help="Watch for new USB insertion.")
    watch.add_argument("--poll-interval-sec", type=float, default=2.0)
    watch.add_argument("--debounce-sec", type=float, default=1.5)
    watch.add_argument("--write-probe", action="store_true", help="Enable small write/read probe.")
    watch.set_defaults(func=cmd_watch)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    code = args.func(args)
    raise SystemExit(code)

