#!/bin/bash

# Development mode - run backend and frontend with hot reload
# Requires dependencies installed locally

set -e

echo "========================================="
echo "  Personal Ops Center - DEV MODE"
echo "========================================="
echo ""

# Check if running in tmux or screen
if [ -z "$TMUX" ] && [ -z "$STY" ]; then
    echo "⚠️  Tip: Run this in tmux/screen for better experience!"
    echo ""
fi

# Check if dependencies are installed
if ! command -v uvicorn &> /dev/null; then
    echo "❌ uvicorn not found! Install dependencies:"
    echo "   pip install -r requirements.txt"
    exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Frontend dependencies not found!"
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

DB_PORT=${DOCKER_DB_PORT:-5643}
API_PORT=${LOCAL_API_PORT:-8101}
FRONTEND_PORT=${LOCAL_FRONTEND_PORT:-3101}

echo "🔧 Starting development mode..."
echo ""
echo "This will start:"
echo "  - Database (Docker)"
echo "  - Backend with hot reload (local)"
echo "  - Frontend with Vite dev server (local)"
echo ""

# Start just the database in Docker
echo "🐳 Starting database..."
docker compose up -d postgres

echo "⏳ Waiting for database..."
sleep 5

# Export environment variables
export DATABASE_URL="postgresql://ops_user:ops_password@localhost:${DB_PORT}/ops_center"
export LOGLEVEL="DEBUG"

# Run migrations
echo "🔄 Running migrations..."
alembic upgrade head

echo ""
echo "========================================="
echo "Starting services in background..."
echo "========================================="
echo ""

# Start backend in background
echo "🚀 Starting backend on http://localhost:${API_PORT}..."
uvicorn backend.api.server:app --reload --host 0.0.0.0 --port "${API_PORT}" > backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Start frontend in background
echo "🚀 Starting frontend on http://localhost:${FRONTEND_PORT}..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "   Frontend PID: $FRONTEND_PID"

echo ""
echo "========================================="
echo "  ✅ Development mode running!"
echo "========================================="
echo ""
echo "🌐 Frontend:  http://localhost:${FRONTEND_PORT}"
echo "🔧 API:       http://localhost:${API_PORT}"
echo "📚 API Docs:  http://localhost:${API_PORT}/docs"
echo ""
echo "📊 Logs:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🛑 To stop:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   docker-compose stop postgres"
echo ""

# Save PIDs to file for easy cleanup
echo "$BACKEND_PID" > .dev.pid
echo "$FRONTEND_PID" >> .dev.pid

# Wait for user interrupt
trap "echo ''; echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; docker compose stop postgres; rm -f .dev.pid; exit" INT TERM

echo "Press Ctrl+C to stop all services..."
wait
