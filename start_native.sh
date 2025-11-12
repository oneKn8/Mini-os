#!/bin/bash

echo "========================================="
echo "  Starting Personal Ops Center (NATIVE)"
echo "========================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "[ERROR] .env file not found!"
    echo "Run: cp env.example .env"
    exit 1
fi

# Load .env
set -a
source .env
set +a

echo "[1/4] Checking PostgreSQL..."
if ! sudo systemctl is-active --quiet postgresql; then
    echo "Starting PostgreSQL service..."
    sudo systemctl start postgresql
fi
echo "[OK] PostgreSQL is running"

echo ""
echo "[2/4] Running database migrations..."
export DATABASE_URL="postgresql://ops_user:ops_password@localhost:5432/ops_center"
alembic upgrade head

echo ""
echo "[3/4] Starting Backend API..."
uvicorn backend.api.server:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
BACKEND_PID=$!
echo "    Backend PID: $BACKEND_PID"
sleep 3

echo ""
echo "[4/4] Starting Frontend..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "    Frontend PID: $FRONTEND_PID"

# Save PIDs
echo "$BACKEND_PID" > .native.pid
echo "$FRONTEND_PID" >> .native.pid

sleep 3

echo ""
echo "========================================="
echo "  Personal Ops Center is running!"
echo "========================================="
echo ""
echo "Frontend:  http://localhost:5173"
echo "API:       http://localhost:8000"
echo "API Docs:  http://localhost:8000/docs"
echo ""
echo "Logs:"
echo "  tail -f backend.log"
echo "  tail -f frontend.log"
echo ""
echo "To stop:"
echo "  ./stop_native.sh"
echo ""
