#!/bin/bash

echo "🚀 Starting Telemetry Data Generator..."
echo "=================================================="

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found. Please install Python 3.7+"
    exit 1
fi

# Check if required packages are installed
echo "📦 Checking required packages..."
$PYTHON_CMD -c "import requests, random, time, uuid" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📥 Installing required packages..."
    $PYTHON_CMD -m pip install requests
fi

# Run the generator
echo "🎯 Running telemetry generator..."
$PYTHON_CMD generate_telemetry.py

echo "✅ Script completed!"
