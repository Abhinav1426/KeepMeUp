#!/usr/bin/env bash
# ============================================================
#  Build the Linux release binary for KeepMeUp.
#  Output: release/KeepMeUp-1.0.0-linux  (+ .tar.gz)
#  Run on Linux (PyInstaller cannot cross-compile).
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
cp "dist/KeepMeUp" "release/KeepMeUp-${VERSION}-linux"
chmod +x "release/KeepMeUp-${VERSION}-linux"
tar -czf "release/KeepMeUp-${VERSION}-linux.tar.gz" -C release "KeepMeUp-${VERSION}-linux"

echo
echo "[done] release/KeepMeUp-${VERSION}-linux"
