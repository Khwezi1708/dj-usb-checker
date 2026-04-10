from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class NormalizedDevice:
    device_id: str
    media_name: str
    mount_point: str | None
    filesystem: str | None
    partition_table: str | None
    partition_count: int
    total_size_bytes: int
    writable: bool
    bus_protocol: str | None
    volume_name: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_disk(
    disk_info: dict[str, Any],
    partition_count: int,
) -> NormalizedDevice:
    return NormalizedDevice(
        device_id=str(disk_info.get("DeviceIdentifier", "")),
        media_name=str(disk_info.get("MediaName", "Unknown")),
        mount_point=disk_info.get("MountPoint"),
        filesystem=disk_info.get("FilesystemName"),
        partition_table=disk_info.get("PartitionMapPartitionScheme"),
        partition_count=partition_count,
        total_size_bytes=int(disk_info.get("TotalSize", 0) or 0),
        writable=bool(disk_info.get("Writable", False)),
        bus_protocol=disk_info.get("BusProtocol"),
        volume_name=disk_info.get("VolumeName"),
    )


def extract_disk_partition_count(list_plist: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for disk in list_plist.get("AllDisksAndPartitions", []):
        disk_id = str(disk.get("DeviceIdentifier", ""))
        partitions = disk.get("Partitions") or []
        counts[disk_id] = len(partitions)
    return counts

