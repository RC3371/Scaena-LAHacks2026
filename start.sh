#!/bin/bash
set -e

echo "=== Scaena OS Startup ==="

if [ ! -f backend/.env ]; then
  if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: Set ANTHROPIC_API_KEY in backend/.env or as an environment variable"
    echo "  cp backend/.env.example backend/.env && then edit it"
    exit 1
  fi
  echo "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY" > backend/.env
fi

echo "[1/4] Installing backend dependencies..."
cd backend
python3 -m pip install -r requirements.txt -q
echo "      Done."

echo "[2/4] Seeding demo data..."
python3 seed_data.py
echo "      Done."

cd ..

echo "[3/4] Installing frontend dependencies..."
cd frontend
npm install --silent
echo "      Done."

cd ..

echo "[4/4] Starting servers..."
echo "      Backend → http://localhost:8000"
echo "      Frontend → http://localhost:5173"
echo ""
echo "      Demo data loaded for local testing"
echo "      Open http://localhost:5173 to create or review an entertainer pipeline"
echo ""

trap 'kill %1 %2 2>/dev/null; exit' SIGINT SIGTERM

cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
cd frontend && npm run dev &

wait
