#!/bin/bash

echo "========================================="
echo "  Starting Personal Ops Center (LOCAL)"
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
API_PORT=${LOCAL_API_PORT:-8101}
FRONTEND_PORT=${LOCAL_FRONTEND_PORT:-3101}

echo "[1/5] Starting PostgreSQL in Docker..."
docker compose up -d postgres

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
export DATABASE_URL="postgresql://ops_user:ops_password@localhost:${DB_PORT}/ops_center"
alembic upgrade head

echo ""
echo "[4/5] Starting Backend API..."
uvicorn backend.api.server:app --host 0.0.0.0 --port "${API_PORT}" --reload > backend.log 2>&1 &
BACKEND_PID=$!
echo "    Backend PID: $BACKEND_PID"
sleep 3

echo ""
echo "[5/5] Starting Frontend..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "    Frontend PID: $FRONTEND_PID"

# Save PIDs
echo "$BACKEND_PID" > .local.pid
echo "$FRONTEND_PID" >> .local.pid

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
echo "  ./stop_local.sh"
echo ""
