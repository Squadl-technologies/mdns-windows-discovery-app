"""Generate the Windows tray/exe icon from the PNG source."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    src = repo_root / "assets" / "mobiles.png"
    dst = repo_root / "assets" / "connectivity_icon.ico"
    image = Image.open(src).convert("RGBA")
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]
    image.save(dst, format="ICO", sizes=sizes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
