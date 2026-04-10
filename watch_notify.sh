#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$SCRIPT_DIR}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$PROJECT_DIR"
export PYTHONPATH="$PROJECT_DIR/src"

exec "$PYTHON_BIN" - <<'PY'
import json
import subprocess
import time

from usb_checker.cli import evaluate, list_external_disks
from usb_checker.collector import DiskutilCollector


def notify(title: str, body: str) -> None:
    subprocess.run(
        ["osascript", "-e", f'display notification "{body}" with title "{title}"'],
        check=False,
    )


def main() -> None:
    collector = DiskutilCollector()
    seen: set[str] = set()
    last_notified: dict[str, float] = {}
    poll_interval_sec = 2.0
    debounce_sec = 1.5

    while True:
        try:
            devices = list_external_disks(collector)
            current_ids = {d["device_id"] for d in devices}
            inserted = current_ids - seen
            now = time.time()

            for device in devices:
                device_id = device["device_id"]
                if device_id not in inserted:
                    continue
                if now - last_notified.get(device_id, 0.0) < debounce_sec:
                    continue

                time.sleep(debounce_sec)
                result = evaluate(device)
                payload = json.dumps(result)
                print(payload, flush=True)

                status = result.get("result", {}).get("status", "UNKNOWN")
                score = result.get("result", {}).get("score", "-")
                name = device.get("volume_name") or device_id
                notify("Pioneer USB Checker", f"{name}: {status} (score {score})")
                last_notified[device_id] = time.time()

            seen = current_ids
        except Exception as exc:  # noqa: BLE001
            print(json.dumps({"watch_error": str(exc)}), flush=True)

        time.sleep(poll_interval_sec)


if __name__ == "__main__":
    main()
PY
