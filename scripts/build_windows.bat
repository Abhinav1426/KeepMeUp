@echo off
REM ============================================================
REM  Build the Windows release executable for KeepMeUp.
REM  Output: release\KeepMeUp-1.0.0-windows.exe
REM  Run on Windows (PyInstaller cannot cross-compile).
REM ============================================================

setlocal
set "VERSION=1.0.0"
cd /d "%~dp0\.."

set "PY="
where py >nul 2>&1 && set "PY=py"
if not defined PY ( where python >nul 2>&1 && set "PY=python" )
if not defined PY (
    echo [ERROR] Python not found on PATH.
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [setup] Creating virtual environment...
    %PY% -m venv .venv || exit /b 1
)
set "VENV_PY=.venv\Scripts\python.exe"

echo [setup] Installing build dependencies...
"%VENV_PY%" -m pip install --upgrade pip || exit /b 1
"%VENV_PY%" -m pip install -r requirements.txt pyinstaller || exit /b 1

echo [build] Running PyInstaller...
"%VENV_PY%" -m PyInstaller --noconfirm --clean KeepMeUp.spec || exit /b 1

if not exist "release" mkdir "release"
copy /y "dist\KeepMeUp.exe" "release\KeepMeUp-%VERSION%-windows.exe" || exit /b 1

echo.
echo [done] release\KeepMeUp-%VERSION%-windows.exe
endlocal
