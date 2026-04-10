from __future__ import annotations

import plistlib
import subprocess
from typing import Any


class DiskutilCollector:
    """Collects device metadata from diskutil plist output."""

    def _run_plist(self, command: str, *args: str) -> dict[str, Any]:
        try:
            proc = subprocess.run(
                ["diskutil", command, "-plist", *args],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or b"").decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"diskutil {command} failed: {stderr or exc}") from exc
        return plistlib.loads(proc.stdout)

    def list_disks(self) -> dict[str, Any]:
        return self._run_plist("list")

    def info(self, identifier: str) -> dict[str, Any]:
        return self._run_plist("info", identifier)

