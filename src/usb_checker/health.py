from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass

from usb_checker.normalizer import NormalizedDevice


@dataclass
class HealthResult:
    warnings: list[str]
    info: list[str]


def quick_health_check(device: NormalizedDevice, enable_write_probe: bool = False) -> HealthResult:
    warnings: list[str] = []
    info: list[str] = []
    if not device.mount_point:
        warnings.append("Drive is not mounted.")
        return HealthResult(warnings=warnings, info=info)

    if not os.path.isdir(device.mount_point):
        warnings.append("Mount point path is not accessible.")
        return HealthResult(warnings=warnings, info=info)

    info.append("Mount point is accessible.")

    if enable_write_probe:
        if not device.writable:
            warnings.append("Drive is not writable, skipping write probe.")
            return HealthResult(warnings=warnings, info=info)
        try:
            with tempfile.NamedTemporaryFile(
                dir=device.mount_point,
                prefix=".usb_checker_probe_",
                delete=False,
            ) as f:
                f.write(b"usb-checker-probe")
                probe_path = f.name
            with open(probe_path, "rb") as f:
                _ = f.read()
            os.unlink(probe_path)
            info.append("Write/read probe succeeded.")
        except OSError:
            warnings.append("Write/read probe failed.")

    return HealthResult(warnings=warnings, info=info)

