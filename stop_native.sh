#!/bin/bash

echo "========================================="
echo "  Stopping Personal Ops Center (NATIVE)"
echo "========================================="
echo ""

if [ -f .native.pid ]; then
    echo "Stopping services..."
    kill $(cat .native.pid) 2>/dev/null
    rm -f .native.pid
    echo "[OK] Backend and Frontend stopped"
else
    echo "[WARN] No PID file found"
    # Try to find and kill processes anyway
    pkill -f "uvicorn backend.api.server:app" 2>/dev/null
    pkill -f "vite" 2>/dev/null
fi

echo ""
echo "[OK] All services stopped!"
echo ""
echo "Note: PostgreSQL service is still running"
echo "To stop PostgreSQL: sudo systemctl stop postgresql"
echo ""
