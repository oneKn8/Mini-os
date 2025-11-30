#!/bin/bash

echo "========================================="
echo "  Stopping Personal Ops Center"
echo "========================================="
echo ""

# Load .env for port info if available
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

COMPOSE_FILE_PATH=${COMPOSE_FILE_PATH:-docker-compose.yaml}

API_PORT=${LOCAL_API_PORT:-8101}
FRONTEND_PORT=${LOCAL_FRONTEND_PORT:-3101}

# Function to kill process on a specific port
kill_port() {
    local port=$1
    local name=$2
    local pid=$(lsof -t -i:$port)
    
    if [ ! -z "$pid" ]; then
        echo "Killing $name on port $port (PID: $pid)..."
        kill -9 $pid 2>/dev/null
        echo "[OK] $name stopped"
    fi
}

# Try stopping via PID file first
if [ -f .ops.pid ]; then
    echo "Stopping services from PID file..."
    # Read PIDs into array
    while IFS= read -r pid; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
        fi
    done < .ops.pid
    rm -f .ops.pid
fi

# Check for legacy PID files just in case
if [ -f .local.pid ]; then
    rm -f .local.pid
fi
if [ -f .native.pid ]; then
    rm -f .native.pid
fi

# Aggressive cleanup: Kill anything listening on our ports
echo "Ensuring ports are clear..."
kill_port $API_PORT "Backend API"
kill_port $FRONTEND_PORT "Frontend"

# Fallback: Kill by process name
pkill -f "uvicorn backend.api.server:app" 2>/dev/null
pkill -f "vite" 2>/dev/null

echo ""
echo "Stopping database..."
if [ -f "$COMPOSE_FILE_PATH" ]; then
    docker compose -f "$COMPOSE_FILE_PATH" stop postgres
else
    echo "Compose file '$COMPOSE_FILE_PATH' not found, skipping Docker stop."
fi

echo ""
echo "[OK] All services stopped and ports cleared!"
echo ""
