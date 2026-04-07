@echo off
echo ================================================
echo AI Navigation Backend Server
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo Python found!
echo.

REM Check if model exists
if not exist "..\best_model\best.pt" (
    echo ERROR: Model file not found!
    echo Expected location: ..\best_model\best.pt
    echo Please ensure the YOLO model is in the correct location
    pause
    exit /b 1
)

echo Model file found!
echo.

REM Check if dependencies are installed
echo Checking dependencies...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r backend_requirements.txt
)

echo.
echo ================================================
echo Starting Backend Server...
echo Server will run on: http://localhost:5000
echo.
echo Keep this window open while using the app!
echo Press Ctrl+C to stop the server
echo ================================================
echo.

python backend_service.py

pause
