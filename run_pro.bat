@echo off
REM ============================================================
REM  KeepMeUp launcher
REM  - Creates a local virtual environment (.venv) on first run
REM  - Installs/updates dependencies from requirements.txt
REM  - Launches the PySide6 app (python -m keepmeup.main)
REM ============================================================

setlocal
cd /d "%~dp0"

REM --- Locate a Python interpreter -----------------------------
set "PY="
where py >nul 2>&1 && set "PY=py"
if not defined PY (
    where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
    echo [ERROR] Python was not found on PATH. Install Python 3.9+ and retry.
    pause
    exit /b 1
)

REM --- Create the virtual environment on first run -------------
if not exist ".venv\Scripts\python.exe" (
    echo [setup] Creating virtual environment...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create the virtual environment.
        pause
        exit /b 1
    )
    set "FRESH=1"
)

set "VENV_PY=.venv\Scripts\python.exe"

REM --- Install dependencies -----------------------------------
REM Only run a full install on a fresh venv; use a marker to skip
REM the (slow) pip step on subsequent launches.
if defined FRESH (
    echo [setup] Installing dependencies...
    "%VENV_PY%" -m pip install --upgrade pip
    "%VENV_PY%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed.
        pause
        exit /b 1
    )
)

REM --- Launch the application ----------------------------------
echo [run] Starting KeepMeUp...
"%VENV_PY%" -m keepmeup.main %*
set "EXITCODE=%ERRORLEVEL%"

if not "%EXITCODE%"=="0" (
    echo.
    echo [exit] KeepMeUp exited with code %EXITCODE%.
    pause
)

endlocal
exit /b %EXITCODE%
