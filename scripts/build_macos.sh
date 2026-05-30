#!/usr/bin/env bash
# ============================================================
#  Build the macOS release app bundle for KeepMeUp.
#  Output: release/KeepMeUp-1.0.0-macos.zip  (zipped .app)
#  Run on macOS (PyInstaller cannot cross-compile).
# ============================================================
set -euo pipefail
VERSION="1.0.0"
cd "$(dirname "$0")/.."

PY="${PYTHON:-python3}"

if [ ! -x ".venv/bin/python" ]; then
    echo "[setup] Creating virtual environment..."
    "$PY" -m venv .venv
fi
VENV_PY=".venv/bin/python"

echo "[setup] Installing build dependencies..."
"$VENV_PY" -m pip install --upgrade pip
"$VENV_PY" -m pip install -r requirements.txt pyinstaller

echo "[build] Running PyInstaller..."
"$VENV_PY" -m PyInstaller --noconfirm --clean KeepMeUp.spec

mkdir -p release
# .app is a directory bundle — distribute it zipped so it stays double-clickable.
( cd dist && ditto -c -k --sequesterRsrc --keepParent "KeepMeUp.app" \
    "../release/KeepMeUp-${VERSION}-macos.zip" )

echo
echo "[done] release/KeepMeUp-${VERSION}-macos.zip"
echo "Note: the app is unsigned. First launch: right-click -> Open, or run"
echo "      'xattr -dr com.apple.quarantine KeepMeUp.app' after unzipping."
