#!/bin/bash

echo "========================================="
echo "  Starting Personal Ops Center"
echo "========================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "[ERROR] .env file not found!"
    echo "Run: cp env.example .env"
    exit 1
fi

set -a
source .env
set +a

DB_PORT=${DOCKER_DB_PORT:-5643}
DB_PASSWORD=${POSTGRES_PASSWORD:-changeme}
API_PORT=${LOCAL_API_PORT:-8101}
FRONTEND_PORT=${LOCAL_FRONTEND_PORT:-3101}

echo "[1/5] Starting PostgreSQL in Docker..."
if ! docker compose up -d postgres; then
    echo "[ERROR] Failed to start Docker container."
    echo "Make sure Docker is running."
    exit 1
fi

echo ""
echo "[2/5] Waiting for database..."
sleep 5

MAX_RETRIES=15
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker compose exec -T postgres pg_isready -U ops_user -d ops_center > /dev/null 2>&1; then
        echo "[OK] Database is ready!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "    Waiting... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "[ERROR] Database failed to start!"
    exit 1
fi

echo ""
echo "[3/5] Running database migrations..."
export DATABASE_URL="postgresql://ops_user:${DB_PASSWORD}@localhost:${DB_PORT}/ops_center"
alembic upgrade head

echo ""
echo "[4/5] Starting Backend API..."
# Kill any existing backend process on this port
fuser -k "${API_PORT}/tcp" >/dev/null 2>&1
uvicorn backend.api.server:app --host 0.0.0.0 --port "${API_PORT}" --reload > backend.log 2>&1 &
BACKEND_PID=$!
echo "    Backend PID: $BACKEND_PID"
sleep 3

echo ""
echo "[5/5] Starting Frontend..."
# Kill any existing frontend process on this port
fuser -k "${FRONTEND_PORT}/tcp" >/dev/null 2>&1
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "    Frontend PID: $FRONTEND_PID"

# Save PIDs
echo "$BACKEND_PID" > .ops.pid
echo "$FRONTEND_PID" >> .ops.pid

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
