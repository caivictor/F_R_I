#!/usr/bin/env bash
set -e

echo "=================================================================="
echo "    F.R.I. - Financial Research & Investment AI Multi-Agent System"
echo "=================================================================="

# Check Python 3.10+
if ! command -v python3 &> /dev/null; then
    echo "[Error] Python 3 is required but not installed."
    exit 1
fi

# Setup Virtual Environment if not present
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "[Init] Creating Python virtual environment in ./venv..."
    python3 -m venv venv
fi

# Determine virtual environment python
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Install dependencies if needed
echo "[Init] Verifying backend dependencies..."
pip install -r requirements.txt --quiet

# Verify or build frontend static distribution
if [ ! -d "frontend/dist" ]; then
    echo "[Init] Building frontend static distribution..."
    if command -v npm &> /dev/null; then
        (cd frontend && npm install && npm run build)
    else
        echo "[Warning] npm not found; frontend static files should be pre-built in frontend/dist."
    fi
fi

# Default environment file
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "[Init] Initializing .env from .env.example..."
    cp .env.example .env
fi

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

echo "=================================================================="
echo " Starting F.R.I. unified single-process application..."
echo " Server URL: http://localhost:${PORT}"
echo " Health check: http://localhost:${PORT}/api/health"
echo "=================================================================="

exec uvicorn backend.app.main:app --host "$HOST" --port "$PORT"
