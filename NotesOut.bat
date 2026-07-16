@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Error: Virtual environment not found
    echo Please run: python -m venv .venv
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

echo Starting NotesOut...
.venv\Scripts\python.exe gui.py

if %errorlevel% neq 0 (
    echo.
    echo Program exited with error: %errorlevel%
    pause
)

