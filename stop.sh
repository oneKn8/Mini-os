#!/bin/bash

echo "========================================="
echo "  Stopping Personal Ops Center"
echo "========================================="
echo ""

echo "🛑 Stopping Docker services..."
docker-compose down

echo ""
echo "✅ All services stopped!"
echo ""
echo "📝 Note: Database data is preserved in Docker volumes."
echo "   To remove all data: docker-compose down -v"
echo ""

