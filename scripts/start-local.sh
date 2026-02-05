#!/bin/bash
# Quick Start Script - Chạy Local để Test
# PlagiarismGuard 2.0

echo "🚀 Starting PlagiarismGuard 2.0 Local Environment..."
echo ""

# Check Docker
echo "📋 Step 1: Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo ""
    echo "Please start Docker Desktop first:"
    echo "  1. Open Docker Desktop app"
    echo "  2. Wait for Docker to start (whale icon in menu bar)"
    echo "  3. Run this script again"
    echo ""
    exit 1
fi
echo "✅ Docker is running"
echo ""

# Start Docker services
echo "📋 Step 2: Starting Docker services (PostgreSQL, Redis, MinIO)..."
docker-compose up -d
echo "⏳ Waiting for services to be ready..."
sleep 10
echo "✅ Docker services started"
echo ""

# Check if backend venv exists
echo "📋 Step 3: Setting up Backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install backend dependencies if needed
if [ ! -f "venv/bin/uvicorn" ]; then
    echo "Installing backend dependencies..."
    pip install -r requirements.txt
fi

# Database tables are auto-created by SQLAlchemy on startup
echo "📋 Step 4: Database tables will be created automatically..."
echo ""

# Start backend in background
echo "📋 Step 5: Starting Backend (port 8000)..."
uvicorn app.main:app --reload --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"
echo ""

# Start Celery worker in background
echo "📋 Step 6: Starting Celery Worker..."
celery -A app.workers.celery_app worker --loglevel=info > ../logs/celery.log 2>&1 &
CELERY_PID=$!
echo "✅ Celery worker started (PID: $CELERY_PID)"
echo ""

cd ..

# Start frontend
echo "📋 Step 7: Starting Frontend (port 3000)..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install --legacy-peer-deps
fi

BROWSER=none npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo ""

cd ..

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 10

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ALL SERVICES STARTED!"
echo ""
echo "🌐 URLs:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📁 Test Files Location:"
echo "   tests/fixtures/samples/"
echo "   - original_ai.txt"
echo "   - plagiarized_copy.txt (100% copy)"
echo "   - paraphrased_ai.txt (60-70% similar)"
echo "   - unrelated_blockchain.txt (different topic)"
echo ""
echo "📊 Test Plan:"
echo "   Open: tests/TEST_PLAN.html"
echo ""
echo "📝 Logs:"
echo "   Backend:  tail -f logs/backend.log"
echo "   Celery:   tail -f logs/celery.log"
echo "   Frontend: tail -f logs/frontend.log"
echo ""
echo "🛑 To Stop All Services:"
echo "   kill $BACKEND_PID $CELERY_PID $FRONTEND_PID"
echo "   docker-compose down"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎯 Ready to test! Open http://localhost:3000 in your browser"
echo ""

# Save PIDs for later
echo "$BACKEND_PID $CELERY_PID $FRONTEND_PID" > .pids
