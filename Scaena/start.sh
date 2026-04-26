#!/bin/bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "=== Scaena Startup ==="

if [ ! -f ".env" ]; then
  cp ".env.example" ".env"
  echo "Created .env from .env.example"
fi

echo "[1/5] Installing Python dependencies..."
python3 -m pip install -r requirements.txt

if [ "${SCAENA_SEED_DEMO:-false}" = "true" ]; then
  echo "[2/5] Seeding demo database..."
  python3 seed.py
else
  echo "[2/5] Skipping demo seed. Set SCAENA_SEED_DEMO=true to load sample data."
fi

echo "[3/5] Installing frontend dependencies..."
cd frontend
npm install
cd "$ROOT_DIR"

echo "[4/5] Starting backend (http://localhost:8000)..."
python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

echo "[5/5] Starting agent bureau and frontend..."
cd agents
python3 bureau.py &
AGENTS_PID=$!
cd "$ROOT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
cd "$ROOT_DIR"

echo "Backend PID: $BACKEND_PID"
echo "Agents PID:  $AGENTS_PID"
echo "Frontend PID:$FRONTEND_PID"
echo "Press Ctrl+C to stop all."

trap 'kill $BACKEND_PID $AGENTS_PID $FRONTEND_PID 2>/dev/null || true' SIGINT SIGTERM
wait
