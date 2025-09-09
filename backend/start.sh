#!/bin/bash
set -e

echo "Starting Restaurant SaaS API..."
echo "Current directory: $(pwd)"
echo "Contents: $(ls -la)"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start the application
echo "Starting uvicorn server..."
PORT=${PORT:-8000}
echo "Using PORT=$PORT"
uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'
