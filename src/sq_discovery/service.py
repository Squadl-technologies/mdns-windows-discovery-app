"""Windows service wrapper for continuous mDNS scanning."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import date
import json
from dataclasses import asdict
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path
import threading

from zeroconf import IPVersion

from .scanner import discover_services


class ScannerService:
    """Cross-platform scanner loop used by the Windows service."""

    _MAX_MISSES = 3

    def __init__(self) -> None:
        self._stop = threading.Event()
        self._seen: dict[str, dict[str, str]] = {}
        self._misses: dict[str, int] = {}
        self._removed_count = 0

    def _device_key(self, service) -> str:
        device_id = service.properties.get("device_id") or service.properties.get("b'device_id'")
        if device_id:
            return device_id
        return "|".join(
            [
                service.service_type,
                service.server or "",
                service.name,
                str(service.port or ""),
            ]
        )

    def _snapshot(self, service) -> dict[str, str]:
        payload = asdict(service)
        payload["properties"] = dict(sorted(service.properties.items()))
        payload["addresses"] = sorted(service.addresses)
        return payload

    def run(self) -> None:
        logging.info("Starting mDNS scanner loop")
        self._write_status()
        self._write_device_inventory()

        try:
            while not self._stop.is_set():
                current_seen: dict[str, dict[str, str]] = {}

                def on_service(service) -> None:
                    key = self._device_key(service)
                    current_seen[key] = self._snapshot(service)

                def on_service_removed(service_type, name) -> None:
                    removed_keys = [key for key, snapshot in self._seen.items() if snapshot.get("name") == name]
                    if not removed_keys:
                        return
                    for key in removed_keys:
                        current_seen.pop(key, None)
                        self._misses.pop(key, None)
                    self._removed_count += len(removed_keys)
                    self._seen = {key: value for key, value in self._seen.items() if key not in removed_keys}
                    self._write_device_inventory()
                    self._write_status(current_seen=current_seen, removed_count=len(removed_keys))

                discover_services(
                    service_types=["_sq._tcp.local."],
                    ip_version=IPVersion.V4Only,
                    stop_event=self._stop,
                    duration=5.0,
                    on_event=logging.info,
                    on_service=on_service,
                    on_service_removed=on_service_removed,
                )
                current_keys = set(current_seen)
                previous_keys = set(self._seen)
                for key in current_keys:
                    self._misses[key] = 0
                for key in previous_keys - current_keys:
                    self._misses[key] = self._misses.get(key, 0) + 1

                updated_seen = dict(self._seen)
                updated_seen.update(current_seen)

                to_remove = [key for key, miss_count in self._misses.items() if miss_count >= self._MAX_MISSES]
                for key in to_remove:
                    updated_seen.pop(key, None)
                    self._misses.pop(key, None)

                if updated_seen != self._seen:
                    self._seen = updated_seen
                    self._write_device_inventory()
                if to_remove:
                    self._removed_count += len(to_remove)
                self._write_status(
                    current_seen=current_seen,
                    removed_count=self._removed_count,
                )
        finally:
            self._stop.set()

    def stop(self) -> None:
        self._stop.set()
        self._write_status(service_running=False)

    def _write_device_inventory(self) -> None:
        root = _service_root()
        path = root / "state" / "devices.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        ordered_devices = [self._seen[key] for key in sorted(self._seen)]
        path.write_text(json.dumps(ordered_devices, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")

    def _write_status(
        self,
        *,
        service_running: bool = True,
        current_seen: dict[str, dict[str, str]] | None = None,
        removed_count: int = 0,
    ) -> None:
        root = _service_root()
        path = root / "state" / "status.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        current_seen = self._seen if current_seen is None else current_seen
        payload = {
            "service_running": service_running,
            "device_count": len(self._seen),
            "devices_found": bool(self._seen),
            "last_scan_count": len(current_seen),
            "removed_count": removed_count,
            "miss_counts": dict(sorted(self._misses.items())),
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")


def _configure_logging(log_path: str | None = None) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_path:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(TimedRotatingFileHandler(path, when="H", interval=1, backupCount=24, encoding="utf-8"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=handlers,
        force=True,
    )


def _service_root() -> Path:
    return Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "sq-discovery"


def _service_day_marker() -> Path:
    return _service_root() / "state" / "service-day.txt"


def _clear_service_state() -> None:
    service_root = _service_root()
    for relative_path in (
        Path("state") / "devices.json",
        Path("state") / "status.json",
    ):
        path = service_root / relative_path
        if path.exists():
            path.unlink()


def _prepare_service_state() -> bool:
    service_root = _service_root()
    marker = _service_day_marker()
    today = date.today().isoformat()
    previous_day = marker.read_text(encoding="utf-8").strip() if marker.exists() else ""
    if previous_day == today:
        return False
    _clear_service_state()
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(today, encoding="utf-8")
    return True


def main(argv: Sequence[str] | None = None) -> int:
    return run_service()


def run_service() -> int:
    service_root = _service_root()
    _configure_logging(str(service_root / "logs" / "sq-discovery-service.log"))
    scanner = ScannerService()
    try:
        scanner.run()
    except KeyboardInterrupt:
        scanner.stop()
    return 0


def run_service_debug() -> int:
    _configure_logging(None)
    scanner = ScannerService()
    try:
        print("starting sq-discovery debug service")
        scanner.run()
    except KeyboardInterrupt:
        scanner.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
