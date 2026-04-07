#!/bin/bash

echo "================================================"
echo "AI Navigation Backend Server"
echo "================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "Python found!"
echo ""

# Check if model exists
if [ ! -f "../best_model/best.pt" ]; then
    echo "ERROR: Model file not found!"
    echo "Expected location: ../best_model/best.pt"
    echo "Please ensure the YOLO model is in the correct location"
    exit 1
fi

echo "Model file found!"
echo ""

# Check if dependencies are installed
echo "Checking dependencies..."
if ! python3 -c "import flask" &> /dev/null; then
    echo "Installing dependencies..."
    pip3 install -r backend_requirements.txt
fi

echo ""
echo "================================================"
echo "Starting Backend Server..."
echo "Server will run on: http://localhost:5000"
echo ""
echo "Keep this terminal open while using the app!"
echo "Press Ctrl+C to stop the server"
echo "================================================"
echo ""

python3 backend_service.py
