#!/bin/bash
# Stop All Services Script

echo "🛑 Stopping PlagiarismGuard 2.0..."
echo ""

# Read PIDs if exists
if [ -f ".pids" ]; then
    read BACKEND_PID CELERY_PID FRONTEND_PID < .pids
    
    echo "Stopping Backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || echo "Backend already stopped"
    
    echo "Stopping Celery (PID: $CELERY_PID)..."
    kill $CELERY_PID 2>/dev/null || echo "Celery already stopped"
    
    echo "Stopping Frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null || echo "Frontend already stopped"
    
    rm .pids
else
    echo "No PID file found, killing by port..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "Port 8000 already free"
    lsof -ti:3000 | xargs kill -9 2>/dev/null || echo "Port 3000 already free"
fi

echo ""
echo "Stopping Docker services..."
docker-compose down

echo ""
echo "✅ All services stopped!"
