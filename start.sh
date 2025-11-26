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
if [ -f .env ]; then
    source .env
fi
set +a

# Use LOCAL_DB_PORT from .env if set, otherwise default to 5433 (your active port)
DB_PORT=${LOCAL_DB_PORT:-5433}
API_PORT=${LOCAL_API_PORT:-8101}
FRONTEND_PORT=${LOCAL_FRONTEND_PORT:-3101}

echo "[1/4] Checking PostgreSQL..."
# Skip systemctl check if we are using a custom port (likely Docker or custom install)
if [ "$DB_PORT" != "5432" ]; then
    echo "Using custom DB port: $DB_PORT"
else
    if ! sudo systemctl is-active --quiet postgresql; then
        echo "Starting PostgreSQL service..."
        sudo systemctl start postgresql
    fi
fi
echo "[OK] PostgreSQL check complete"

echo ""
echo "[2/4] Running database migrations..."
# Ensure DATABASE_URL matches the port we found
export DATABASE_URL="postgresql://ops_user:ops_password@localhost:${DB_PORT}/ops_center"
alembic upgrade head

echo ""
echo "[3/4] Starting Backend API..."
uvicorn backend.api.server:app --host 0.0.0.0 --port "${API_PORT}" --reload > backend.log 2>&1 &
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
echo "Frontend:  http://localhost:${FRONTEND_PORT}"
echo "API:       http://localhost:${API_PORT}"
echo "API Docs:  http://localhost:${API_PORT}/docs"
echo ""
echo "Logs:"
echo "  tail -f backend.log"
echo "  tail -f frontend.log"
echo ""
echo "To stop:"
echo "  ./stop.sh"
echo ""
