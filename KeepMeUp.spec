# -*- mode: python ; coding: utf-8 -*-
"""
Cross-platform PyInstaller spec for KeepMeUp.

Run on the *target* OS (PyInstaller cannot cross-compile):

    pyinstaller --noconfirm KeepMeUp.spec

Produces:
  - Windows : dist/KeepMeUp.exe        (single windowed executable)
  - Linux   : dist/KeepMeUp            (single executable)
  - macOS   : dist/KeepMeUp.app        (application bundle)
"""

import sys

APP_NAME = "KeepMeUp"

# Bundle content.txt (and any future assets) at the root of the package so the
# frozen app can find it via sys._MEIPASS (see keepmeup/main.py).
datas = [("content.txt", ".")]

a = Analysis(
    ["keepmeup/main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # GUI app — no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# On macOS wrap the executable in a proper .app bundle.
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name=f"{APP_NAME}.app",
        icon=None,
        bundle_identifier="com.abhinav.keepmeup",
        info_plist={
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "1.0.0",
            "NSHighResolutionCapable": True,
            # KeepMeUp drives the mouse/keyboard; macOS requires this string for
            # the Accessibility permission prompt.
            "NSAppleEventsUsageDescription":
                "KeepMeUp simulates mouse and keyboard activity.",
        },
    )
