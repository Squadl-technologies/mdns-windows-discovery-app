# -*- mode: python ; coding: utf-8 -*-
from os import getcwd
from pathlib import Path

block_cipher = None
project_root = Path(getcwd()).resolve()
src_path = project_root / "src"

a = Analysis(
    [str(src_path / "sq_discovery" / "tray.py")],
    pathex=[str(src_path)],
    binaries=[],
    datas=[(str(project_root / "assets" / "mobiles.png"), "assets")],
    hiddenimports=[
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",
        "PIL.ImageFont",
        "pystray",
        "sq_discovery",
        "sq_discovery.service",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="sq-discovery-tray",
    icon=str(project_root / "assets" / "connectivity_icon.ico"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
