#!/bin/bash

echo "========================================="
echo "  Personal Ops Center - Status"
echo "========================================="
echo ""

if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

API_PORT=${HOST_API_PORT:-8101}
FRONTEND_PORT=${HOST_FRONTEND_PORT:-3101}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    exit 1
fi

echo "🐳 Docker Services:"
docker compose ps

echo ""
echo "🔍 Service Health:"
echo ""

# Check database
if docker compose exec -T postgres pg_isready -U ops_user -d ops_center > /dev/null 2>&1; then
    echo "✅ Database: Running"
else
    echo "❌ Database: Not responding"
fi

# Check backend API
if curl -sf http://localhost:${API_PORT}/health > /dev/null 2>&1; then
    echo "✅ Backend API: Running (http://localhost:${API_PORT})"
else
    echo "❌ Backend API: Not responding (http://localhost:${API_PORT})"
fi

# Check frontend
if curl -sf http://localhost:${FRONTEND_PORT} > /dev/null 2>&1; then
    echo "✅ Frontend: Running (http://localhost:${FRONTEND_PORT})"
else
    echo "❌ Frontend: Not responding (http://localhost:${FRONTEND_PORT})"
fi

echo ""
