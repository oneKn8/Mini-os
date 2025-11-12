#!/bin/bash

set -e

echo "========================================="
echo "  Starting Personal Ops Center"
echo "========================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Creating .env from env.example..."
    cp env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your NVIDIA_API_KEY before continuing!"
    echo "Press Enter to continue or Ctrl+C to exit..."
    read
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

echo "🐳 Starting Docker services..."
docker compose up -d

echo ""
echo "⏳ Waiting for database to be ready..."
sleep 5

# Wait for database to be healthy
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker compose exec -T postgres pg_isready -U ops_user -d ops_center > /dev/null 2>&1; then
        echo "✅ Database is ready!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Waiting for database... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Database failed to start in time!"
    exit 1
fi

echo ""
echo "🔄 Running database migrations..."
docker compose exec -T backend-api alembic upgrade head

echo ""
echo "========================================="
echo "  ✅ Personal Ops Center is running!"
echo "========================================="
echo ""
echo "🌐 Frontend:  http://localhost:3001"
echo "🔧 API:       http://localhost:8001"
echo "📚 API Docs:  http://localhost:8001/docs"
echo "💚 Health:    http://localhost:8001/health"
echo ""
echo "📊 View logs:"
echo "   docker compose logs -f backend-api"
echo "   docker compose logs -f frontend"
echo ""
echo "🛑 To stop: ./stop.sh"
echo ""
echo "🌐 URLs:"
echo "   Frontend:  http://localhost:3001"
echo "   API:       http://localhost:8001"
echo "   API Docs:  http://localhost:8001/docs"
echo ""

