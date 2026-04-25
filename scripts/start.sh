#!/usr/bin/env bash
set -euo pipefail

echo "=== 拾途 (Shí Tú) Startup ==="

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠ Please edit .env and add your API keys (DEEPSEEK_API_KEY, AMAP_API_KEY)"
fi

echo "Building containers..."
docker compose build

echo "Starting services..."
docker compose up -d

echo "Waiting for backend..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "Backend is healthy"
        break
    fi
    sleep 1
done

echo ""
echo "=== Ready ==="
echo "Frontend: http://localhost"
echo "Backend:  http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
