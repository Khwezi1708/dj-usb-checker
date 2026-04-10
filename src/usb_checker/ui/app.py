from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from usb_checker.cli import evaluate, list_external_disks
from usb_checker.collector import DiskutilCollector

INDEX_HTML = """<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Pioneer USB Checker</title>
    <style>
      :root {
        color-scheme: light dark;
        --bg: #0f172a;
        --card: #111827;
        --muted: #94a3b8;
        --text: #e5e7eb;
        --accent: #38bdf8;
        --ok: #22c55e;
        --warn: #f59e0b;
        --fail: #ef4444;
        --border: #1f2937;
      }
      body {
        margin: 0;
        background: linear-gradient(180deg, #0b1220, #111827);
        color: var(--text);
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }
      .container {
        max-width: 1100px;
        margin: 0 auto;
        padding: 2rem 1.25rem 3rem;
      }
      .title {
        margin: 0 0 0.25rem;
        font-size: 2rem;
        letter-spacing: 0.2px;
      }
      .subtitle {
        margin: 0 0 1.25rem;
        color: var(--muted);
      }
      .toolbar {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
      }
      .btn {
        border: 1px solid #0ea5e9;
        background: rgba(14, 165, 233, 0.15);
        color: #bae6fd;
        border-radius: 10px;
        padding: 0.6rem 0.95rem;
        font-weight: 600;
        cursor: pointer;
      }
      .btn:hover { background: rgba(14, 165, 233, 0.25); }
      .grid {
        display: grid;
        grid-template-columns: 1.1fr 1fr;
        gap: 1rem;
      }
      .card {
        background: rgba(17, 24, 39, 0.95);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1rem;
        box-shadow: 0 12px 30px rgba(0,0,0,0.25);
      }
      .card h2 {
        margin: 0 0 0.8rem;
        font-size: 1rem;
        color: #d1d5db;
      }
      .devices {
        display: grid;
        gap: 0.6rem;
      }
      .devices-group {
        display: grid;
        gap: 0.6rem;
      }
      .group-title {
        margin: 0.4rem 0 0.25rem;
        font-size: 0.82rem;
        color: #93c5fd;
        text-transform: uppercase;
        letter-spacing: 0.08em;
      }
      .device-btn {
        width: 100%;
        text-align: left;
        border: 1px solid #334155;
        background: #0b1220;
        color: #e2e8f0;
        border-radius: 10px;
        padding: 0.7rem 0.8rem;
        cursor: pointer;
      }
      .device-btn:hover { border-color: #38bdf8; }
      .device-name {
        font-weight: 600;
      }
      .device-meta {
        font-size: 0.82rem;
        color: var(--muted);
      }
      .device-type {
        display: inline-block;
        margin-top: 0.35rem;
        font-size: 0.74rem;
        border-radius: 999px;
        padding: 0.14rem 0.5rem;
        border: 1px solid #1d4ed8;
        color: #93c5fd;
        background: rgba(37, 99, 235, 0.15);
      }
      .device-btn.grayed {
        opacity: 0.55;
        filter: grayscale(20%);
        border-color: #374151;
      }
      .device-btn.grayed .device-type {
        border-color: #6b7280;
        color: #cbd5e1;
        background: rgba(107, 114, 128, 0.2);
      }
      .hint {
        color: #9ca3af;
        font-size: 0.82rem;
        margin-top: 0.25rem;
      }
      .status-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.8rem;
      }
      .badge {
        font-size: 0.8rem;
        font-weight: 700;
        border-radius: 999px;
        padding: 0.25rem 0.6rem;
        border: 1px solid transparent;
      }
      .pass { color: #86efac; border-color: rgba(34, 197, 94, 0.5); background: rgba(34, 197, 94, 0.1); }
      .warn { color: #fcd34d; border-color: rgba(245, 158, 11, 0.5); background: rgba(245, 158, 11, 0.1); }
      .fail { color: #fca5a5; border-color: rgba(239, 68, 68, 0.5); background: rgba(239, 68, 68, 0.1); }
      .score {
        color: #93c5fd;
        font-weight: 600;
      }
      .list {
        margin: 0.4rem 0 0.9rem;
        padding-left: 1.1rem;
      }
      .list li { margin: 0.35rem 0; }
      pre {
        margin: 0;
        background: #0b1220;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 0.8rem;
        white-space: pre-wrap;
        max-height: 310px;
        overflow: auto;
      }
      .placeholder {
        color: var(--muted);
        font-size: 0.92rem;
      }
      @media (max-width: 900px) {
        .grid { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <div class="container">
      <h1 class="title">Pioneer USB Checker</h1>
      <p class="subtitle">Strict FAT32 compatibility checks for DJ-ready USB drives.</p>
      <div class="toolbar">
        <button class="btn" onclick="loadDevices()">Refresh Devices</button>
        <span id="deviceCount" class="subtitle"></span>
      </div>
      <div class="grid">
        <section class="card">
          <h2>Detected Devices</h2>
          <p class="hint">USB sticks are prioritized. Other external media is shown grayed out.</p>
          <div id="devices" class="devices"></div>
        </section>
        <section class="card">
          <div class="status-row">
            <h2>Check Result</h2>
            <span id="statusBadge" class="badge">NO RESULT</span>
          </div>
          <div id="summary" class="placeholder">Select a device to run compatibility checks.</div>
          <h2 style="margin-top: 1rem;">Raw JSON</h2>
          <pre id="result">{}</pre>
        </section>
      </div>
    </div>
    <script>
      function statusClass(status) {
        if (status === 'PASS') return 'badge pass';
        if (status === 'WARN') return 'badge warn';
        if (status === 'FAIL') return 'badge fail';
        return 'badge';
      }

      function classifyDevice(device) {
        const bus = (device.bus_protocol || '').toLowerCase();
        const media = (device.media_name || '').toLowerCase();
        if (bus.includes('usb') && !media.includes('disk image')) {
          return { key: 'usb', label: 'USB Stick', grayed: false };
        }
        if (media.includes('disk image') || bus.includes('disk image')) {
          return { key: 'image', label: 'Disk Image', grayed: true };
        }
        return { key: 'other', label: 'Other External', grayed: true };
      }

      function makeGroup(title) {
        const wrapper = document.createElement('div');
        wrapper.className = 'devices-group';
        const heading = document.createElement('div');
        heading.className = 'group-title';
        heading.textContent = title;
        wrapper.appendChild(heading);
        return wrapper;
      }

      async function loadDevices() {
        const res = await fetch('/api/devices');
        const data = await res.json();
        const el = document.getElementById('devices');
        el.innerHTML = '';
        document.getElementById('deviceCount').textContent = data.devices.length + ' device(s)';

        if (!data.devices.length) {
          const p = document.createElement('p');
          p.className = 'placeholder';
          p.textContent = 'No external devices found.';
          el.appendChild(p);
          return;
        }

        const usbGroup = makeGroup('USB Sticks');
        const otherGroup = makeGroup('Other External Media');
        let usbCount = 0;
        let otherCount = 0;

        for (const d of data.devices) {
          const classification = classifyDevice(d);
          const b = document.createElement('button');
          b.className = 'device-btn';
          if (classification.grayed) {
            b.classList.add('grayed');
          }
          b.onclick = () => runCheck(d.device_id);
          const fs = d.filesystem || 'unknown fs';
          const protocol = d.bus_protocol || 'unknown bus';
          const displayName = (d.volume_name && d.volume_name.trim()) ? d.volume_name : d.device_id;
          b.innerHTML = '<div class="device-name">' + displayName + '</div>' +
                        '<div class="device-meta">' + d.device_id + '</div>' +
                        '<div class="device-meta">' + fs + ' • ' + protocol + '</div>' +
                        '<span class="device-type">' + classification.label + '</span>';

          if (classification.key === 'usb') {
            usbGroup.appendChild(b);
            usbCount += 1;
          } else {
            otherGroup.appendChild(b);
            otherCount += 1;
          }
        }

        if (usbCount > 0) {
          el.appendChild(usbGroup);
        }
        if (otherCount > 0) {
          el.appendChild(otherGroup);
        }
      }

      async function runCheck(deviceId) {
        const res = await fetch('/api/check?device=' + encodeURIComponent(deviceId));
        const data = await res.json();
        const result = data.result || {};
        const status = result.status || 'NO RESULT';
        const badge = document.getElementById('statusBadge');
        badge.className = statusClass(status);
        badge.textContent = status;

        const reasons = result.reasons || [];
        const warnings = result.warnings || [];
        const summary = document.getElementById('summary');
        summary.innerHTML =
          '<div class="score">Score: ' + (result.score ?? '-') + '</div>' +
          '<div><strong>Reasons</strong></div>' +
          '<ul class="list">' +
          (reasons.length ? reasons.map(r => '<li>' + r + '</li>').join('') : '<li>None</li>') +
          '</ul>' +
          '<div><strong>Warnings</strong></div>' +
          '<ul class="list">' +
          (warnings.length ? warnings.map(w => '<li>' + w + '</li>').join('') : '<li>None</li>') +
          '</ul>';

        document.getElementById('result').textContent = JSON.stringify(data, null, 2);
      }
      loadDevices();
    </script>
  </body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    collector = DiskutilCollector()

    def _json(self, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            body = INDEX_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/api/devices":
            self._json({"devices": list_external_disks(self.collector)})
            return
        if parsed.path == "/api/check":
            device_id = parse_qs(parsed.query).get("device", [""])[0]
            for device in list_external_disks(self.collector):
                if device["device_id"] == device_id:
                    self._json(evaluate(device))
                    return
            self._json({"error": f"Device {device_id} not found"})
            return
        self.send_response(404)
        self.end_headers()


def main() -> None:
    server = HTTPServer(("127.0.0.1", 8765), Handler)
    print("UI running at http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()

