#!/bin/bash

echo "========================================="
echo "  Stopping Personal Ops Center (LOCAL)"
echo "========================================="
echo ""

if [ -f .local.pid ]; then
    echo "Stopping services..."
    kill $(cat .local.pid) 2>/dev/null
    rm -f .local.pid
    echo "[OK] Backend and Frontend stopped"
else
    echo "[WARN] No PID file found"
fi

echo ""
echo "Stopping database..."
docker compose stop postgres

echo ""
echo "[OK] All services stopped!"
echo ""
