#!/bin/bash
# Development run script for PlagiarismGuard 2.0
# Starts both backend and frontend concurrently

set -e  # Exit on error

echo "🚀 Starting PlagiarismGuard 2.0 in development mode..."
echo ""

# Check if Docker services are running
if ! docker-compose ps | grep -q "Up"; then
    echo "🐳 Starting Docker services..."
    docker-compose up -d
    echo "   Waiting for services to be ready..."
    sleep 5
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "✅ Services stopped"
    exit 0
}

# Trap Ctrl+C and other termination signals
trap cleanup INT TERM

# Start backend
echo "🐍 Starting backend on http://localhost:8000..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend
echo "⚛️  Starting frontend on http://localhost:3000..."
cd frontend
BROWSER=none npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 5

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Application running!"
echo ""
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "   Logs:"
echo "   Backend:   tail -f logs/backend.log"
echo "   Frontend:  tail -f logs/frontend.log"
echo ""
echo "Press Ctrl+C to stop all services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
