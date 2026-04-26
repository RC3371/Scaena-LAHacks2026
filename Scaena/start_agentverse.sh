#!/bin/bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if [ ! -f ".env" ]; then
  cp ".env.example" ".env"
  echo "Created .env from .env.example"
fi

echo "=== Scaena Agentverse Bridge ==="
echo "Starts real mailbox uAgents for ASI:One / Agentverse chat."
echo "Keep Scaena running in another terminal with ./start.sh."

python3 agentverse/agentverse_bridge.py
