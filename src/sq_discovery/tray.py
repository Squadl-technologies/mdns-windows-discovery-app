"""Windows tray companion for sq-discovery."""

from __future__ import annotations

import json
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from time import sleep

from PIL import Image, ImageDraw

try:
    from sq_discovery.service import _service_root
except ImportError:  # pragma: no cover - PyInstaller script execution fallback
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from sq_discovery.service import _service_root

try:
    import pystray
except ImportError as exc:  # pragma: no cover - optional dependency
    raise RuntimeError("pystray is required for the tray app") from exc


@dataclass(slots=True)
class TrayStatus:
    service_running: bool = False
    device_count: int = 0
    devices_found: bool = False


def _load_base_icon() -> Image.Image:
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    icon_path = base_dir / "assets" / "mobiles.png"
    return Image.open(icon_path).convert("RGBA")


def _overlay_mark(base: Image.Image, color: tuple[int, int, int, int], mark: str) -> Image.Image:
    icon = base.copy().resize((256, 256), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(icon)
    radius = 64
    center = (198, 198)
    draw.ellipse((center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius), fill=color)
    if mark == "check":
        draw.line((center[0] - 26, center[1] + 2, center[0] - 6, center[1] + 22), fill=(255, 255, 255, 255), width=12)
        draw.line((center[0] - 6, center[1] + 22, center[0] + 28, center[1] - 18), fill=(255, 255, 255, 255), width=12)
    else:
        draw.line((center[0] - 22, center[1] - 22, center[0] + 22, center[1] + 22), fill=(255, 255, 255, 255), width=12)
        draw.line((center[0] + 22, center[1] - 22, center[0] - 22, center[1] + 22), fill=(255, 255, 255, 255), width=12)
    return icon


def _build_icon(status: TrayStatus) -> Image.Image:
    base = _load_base_icon()
    if not status.service_running:
        return _overlay_mark(base, (120, 120, 120, 255), "cross")
    if status.devices_found:
        return _overlay_mark(base, (22, 163, 74, 255), "check")
    return _overlay_mark(base, (220, 38, 38, 255), "cross")


def _read_status() -> TrayStatus:
    status_path = _service_root() / "state" / "status.json"
    if not status_path.exists():
        return TrayStatus()
    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return TrayStatus()
    return TrayStatus(
        service_running=bool(payload.get("service_running")),
        device_count=int(payload.get("device_count") or 0),
        devices_found=bool(payload.get("devices_found")),
    )


def _tooltip(status: TrayStatus) -> str:
    if not status.service_running:
        return "sq-discovery: service stopped"
    if status.devices_found:
        return f"sq-discovery: {status.device_count} device(s) found"
    return "sq-discovery: no devices found"


def main() -> int:
    current_status = _read_status()
    icon = pystray.Icon("sq-discovery", _build_icon(current_status), _tooltip(current_status))
    stop_event = threading.Event()

    def refresh() -> None:
        nonlocal current_status
        while not stop_event.is_set():
            new_status = _read_status()
            if new_status != current_status:
                current_status = new_status
                icon.icon = _build_icon(new_status)
                icon.title = _tooltip(new_status)
                icon.visible = True
            sleep(1)

    def quit_action(icon_obj, item) -> None:
        stop_event.set()
        icon_obj.stop()

    icon.menu = pystray.Menu(pystray.MenuItem("Quit", quit_action))
    watcher = threading.Thread(target=refresh, daemon=True)
    watcher.start()
    icon.run()
    stop_event.set()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
