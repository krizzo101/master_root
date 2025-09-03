#!/bin/bash

# Claude Monitor Backend Service Startup Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting Claude Monitoring Service..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check database exists
DB_PATH="/home/opsvi/master_root/chat_logs.db"
if [ ! -f "$DB_PATH" ]; then
    echo "WARNING: Database not found at $DB_PATH"
    echo "Service will start but some features may not work properly."
fi

# Start the service
echo "Starting monitoring service on http://0.0.0.0:8000"
echo "WebSocket endpoint available at ws://0.0.0.0:8000/ws"
echo "API documentation at http://0.0.0.0:8000/docs"
echo ""
echo "Press Ctrl+C to stop the service"

python monitoring_service.py
