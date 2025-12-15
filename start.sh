#!/bin/bash

# PlagiarismGuard 2.0 - Startup Script
# Tự động khởi động Backend + Frontend

echo "🚀 Starting PlagiarismGuard 2.0..."
echo "=================================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create logs directory
mkdir -p logs

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    pkill -f "uvicorn app.main:app"
    pkill -f "react-scripts start"
    echo "✅ All services stopped"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT TERM

# Check if Redis is running
echo ""
echo "📊 Checking Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis is not running. Starting Redis..."
    
    # Try to start Redis
    if command -v redis-server > /dev/null 2>&1; then
        # Start Redis in background
        redis-server --daemonize yes --port 6379 > /dev/null 2>&1
        sleep 2
        
        if redis-cli ping > /dev/null 2>&1; then
            echo "✅ Redis started successfully"
        else
            echo "❌ Failed to start Redis!"
            echo "   Please install Redis:"
            echo "   brew install redis"
            exit 1
        fi
    else
        echo "❌ Redis is not installed!"
        echo "   Please install Redis:"
        echo "   brew install redis"
        exit 1
    fi
else
    echo "✅ Redis is already running"
fi

# Start Backend
echo ""
echo "🔧 Starting Backend..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..
echo "✅ Backend started (PID: $BACKEND_PID)"
echo "   URL: http://localhost:8000"
echo "   Logs: logs/backend.log"

# Wait for backend to be ready
echo ""
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    sleep 1
    echo -n "."
done

# Start Frontend
echo ""
echo "⚛️  Starting Frontend..."
cd frontend
BROWSER=none npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo "   URL: http://localhost:3000"
echo "   Logs: logs/frontend.log"

# Wait for frontend to be ready
echo ""
echo "⏳ Waiting for frontend to be ready..."
for i in {1..60}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend is ready!"
        break
    fi
    sleep 1
    echo -n "."
done

# Open browser
echo ""
echo "🌐 Opening browser..."
sleep 2
open http://localhost:3000

# Show status
echo ""
echo "=================================="
echo "✅ PlagiarismGuard 2.0 is running!"
echo "=================================="
echo ""
echo "📍 URLs:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📊 Corpus Stats:"
curl -s http://localhost:8000/api/v1/plagiarism/corpus/stats | python3 -m json.tool 2>/dev/null || echo "   (API not ready yet)"
echo ""
echo "📝 Logs:"
echo "   Backend:  tail -f logs/backend.log"
echo "   Frontend: tail -f logs/frontend.log"
echo ""
echo "🛑 Press Ctrl+C to stop all services"
echo ""

# Keep script running
wait
