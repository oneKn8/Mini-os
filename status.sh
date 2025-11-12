#!/bin/bash

echo "========================================="
echo "  Personal Ops Center - Status"
echo "========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    exit 1
fi

echo "🐳 Docker Services:"
docker-compose ps

echo ""
echo "🔍 Service Health:"
echo ""

# Check database
if docker-compose exec -T postgres pg_isready -U ops_user -d ops_center > /dev/null 2>&1; then
    echo "✅ Database: Running"
else
    echo "❌ Database: Not responding"
fi

# Check backend API
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API: Running (http://localhost:8000)"
else
    echo "❌ Backend API: Not responding (http://localhost:8000)"
fi

# Check frontend
if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend: Running (http://localhost:3000)"
else
    echo "❌ Frontend: Not responding (http://localhost:3000)"
fi

echo ""

