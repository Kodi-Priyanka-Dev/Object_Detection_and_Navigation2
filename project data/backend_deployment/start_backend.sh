#!/bin/bash

# Linux/Mac startup script for backend

echo "================================================"
echo "Navigation Backend - Startup Script (Linux/Mac)"
echo "================================================"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set environment variables
export FLASK_APP=unified_server.py
export FLASK_ENV=production
export PORT=5000

# Run the backend
echo ""
echo "================================================"
echo "Starting Backend on http://localhost:5000"
echo "================================================"
echo ""
python unified_server.py
