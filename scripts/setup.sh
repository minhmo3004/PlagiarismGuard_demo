#!/bin/bash
# Setup script for PlagiarismGuard 2.0
# Installs all dependencies for backend and frontend

set -e  # Exit on error

echo "🚀 Setting up PlagiarismGuard 2.0..."
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "   Please install Python 3.9+ from https://www.python.org/"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    echo "   Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed."
    echo "   Please install Docker from https://www.docker.com/"
    exit 1
fi

echo "✅ All prerequisites found"
echo ""

# Backend setup
echo "📦 Installing backend dependencies..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "   Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "   Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "   Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

cd ..
echo "✅ Backend dependencies installed"
echo ""

# Frontend setup
echo "📦 Installing frontend dependencies..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "   Installing npm packages..."
    npm install
else
    echo "   node_modules exists, skipping npm install"
fi

cd ..
echo "✅ Frontend dependencies installed"
echo ""

# Docker services
echo "🐳 Starting Docker services (PostgreSQL, Redis)..."
if docker-compose ps | grep -q "Up"; then
    echo "   Docker services already running"
else
    docker-compose up -d
    echo "   Waiting for PostgreSQL to be ready..."
    sleep 10
fi
echo "✅ Docker services started"
echo ""

# Database migrations
echo "🗄️  Running database migrations..."
cd backend
source venv/bin/activate

# Check if alembic is configured
if [ -f "alembic.ini" ]; then
    alembic upgrade head
    echo "✅ Database migrations complete"
else
    echo "⚠️  No alembic.ini found, skipping migrations"
fi

cd ..
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Start the application:"
echo "     ./scripts/run-dev.sh"
echo ""
echo "  2. Access the application:"
echo "     Frontend:  http://localhost:3000"
echo "     Backend:   http://localhost:8000"
echo "     API Docs:  http://localhost:8000/docs"
echo ""
echo "  3. Run tests:"
echo "     ./scripts/run-tests.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
