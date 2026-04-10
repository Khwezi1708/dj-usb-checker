# Pioneer USB Checker

Pioneer USB Checker is a macOS-first tool that validates whether a USB drive is likely to work on Pioneer DJ gear, with strict FAT32-focused compatibility rules.

It includes:
- a CLI for scanning, checking, and watch-mode auto checks
- a lightweight local web UI for quick visual inspection
- an optional background notifier script for USB insert events

## Features

- Detect external drives via `diskutil`
- Enforce Pioneer-safe hard rules:
  - FAT32 filesystem
  - MBR partition table
  - single partition
- Run quick health checks:
  - mounted and accessible
  - optional write/read probe
- Return deterministic statuses: `PASS`, `WARN`, `FAIL`
- Watch mode for auto-checking newly inserted drives

## Platform Support

- macOS: supported (primary target)
- Linux/Windows: not currently supported

## Requirements

- Python 3.11+
- macOS with `diskutil` available

## Installation

Clone and install locally:

```bash
git clone <your-repo-url>
cd usb-checker
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

You can also run without installation:

```bash
PYTHONPATH=src python3 -m usb_checker.cli scan
```

## Usage

### 1) Scan external disks

```bash
usb-checker scan
```

### 2) Check a specific disk

```bash
usb-checker check disk6
```

Optional write probe:

```bash
usb-checker check disk6 --write-probe
```

### 3) Watch for newly inserted USB drives

```bash
usb-checker watch --poll-interval-sec 2 --debounce-sec 1.5
```

### 4) Run local web UI

```bash
usb-checker-ui
```

Open:

- [http://127.0.0.1:8765](http://127.0.0.1:8765)

## Rule Logic

Hard failures (`FAIL`) are triggered when any of these fail:
- filesystem is not FAT32 (`MS-DOS FAT32` or `FAT32`)
- partition table is not MBR (`Master Boot Record` or `FDisk_partition_scheme`)
- partition count is not `1`

Warnings (`WARN`) may be triggered by:
- drive size above conservative threshold
- non-ASCII or long volume labels
- health warnings (for example, drive not mounted)

`PASS` means no hard failures and no warnings.

## Project Structure

```text
usb-checker/
  src/usb_checker/
    cli.py
    collector.py
    normalizer.py
    health.py
    scoring.py
    rules/
      engine.py
      pioneer_profiles.json
    ui/
      app.py
  tests/
    fixtures/
    test_rules_engine.py
  watch_notify.sh
```

## Development

Run tests:

```bash
PYTHONPATH=src python3 -m pytest -q
```

## LaunchAgent (Optional)

Use `watch_notify.sh` with a user LaunchAgent if you want background USB notifications on insert.

Note: paths in LaunchAgent files are machine-specific and should not be committed in this repository.

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Add tests for your change
4. Open a pull request with clear context

## Security

Please do not include personal data, mount paths, or logs with sensitive identifiers in public issues.

## License

MIT. See [`LICENSE`](LICENSE).
