#!/bin/bash
# Ollama Server - macOS/Linux launch script

cd "$(dirname "$0")"

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "Error: Python not found. Please install Python 3."
    exit 1
fi

# Check if dependencies are installed
if ! $PYTHON -c "import fastapi, uvicorn, httpx" 2>/dev/null; then
    echo "Installing dependencies..."
    $PYTHON -m pip install -r requirements.txt
fi

# Create config.json from example if it doesn't exist
if [ ! -f config.json ]; then
    echo "Creating config.json from example..."
    cp config.example.json config.json
fi

# Start the server
echo "Starting Ollama Server..."
echo "Web UI: http://localhost:11435"
echo "Press Ctrl+C to stop"
echo ""

$PYTHON -m uvicorn app.main:app --host 0.0.0.0 --port 11435
