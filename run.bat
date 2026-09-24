@echo off
REM ==============================================================================
REM Customer360 Intelligence Platform - 1-Click Windows Launcher
REM ==============================================================================

echo [Customer360] Starting end-to-end analytics pipeline...
echo.

cd /d "%~dp0"

IF EXIST ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) ELSE (
    echo [ERROR] Virtual environment not found in .venv.
    echo Please ensure the project was initialized properly.
    pause
    exit /b 1
)

echo.
echo [Customer360] Pipeline finished! Press any key to close this window.
pause
