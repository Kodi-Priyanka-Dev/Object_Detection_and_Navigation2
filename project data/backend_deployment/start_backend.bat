@echo off
REM Windows startup script for backend

echo ================================================
echo Navigation Backend - Startup Script (Windows)
echo ================================================

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Set environment variables
set FLASK_APP=unified_server.py
set FLASK_ENV=production
set PORT=5000

REM Run the backend
echo.
echo ================================================
echo Starting Backend on http://localhost:5000
echo ================================================
echo.
python unified_server.py

pause
