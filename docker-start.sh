#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# PlagiarismGuard 2.0 - Docker Startup Script
# ═══════════════════════════════════════════════════════════════

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}       PlagiarismGuard 2.0 - Docker Deployment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Function to use the correct docker-compose command
docker_compose() {
    if docker compose version &> /dev/null; then
        docker compose "$@"
    else
        docker-compose "$@"
    fi
}

# Parse arguments
INIT_CORPUS=false
BUILD=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --init-corpus) INIT_CORPUS=true ;;
        --build) BUILD=true ;;
        --help)
            echo "Usage: ./docker-start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --build         Rebuild all images"
            echo "  --init-corpus   Generate 3000 Vietnamese documents after startup"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

# Step 1: Build images if needed
if [ "$BUILD" = true ]; then
    echo -e "\n${YELLOW}📦 Building Docker images...${NC}"
    docker_compose build
fi

# Step 2: Start infrastructure services first
echo -e "\n${YELLOW}🚀 Starting infrastructure services (Redis, PostgreSQL, MinIO)...${NC}"
docker_compose up -d redis postgres minio

# Wait for services to be healthy
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Step 3: Start application services
echo -e "\n${YELLOW}🚀 Starting application services (Backend, Frontend)...${NC}"
docker_compose up -d backend frontend

# Step 4: Initialize corpus if requested
if [ "$INIT_CORPUS" = true ]; then
    echo -e "\n${YELLOW}⏳ Waiting for backend to be ready...${NC}"
    sleep 15
    
    echo -e "\n${YELLOW}📚 Generating Vietnamese corpus (3000 documents)...${NC}"
    echo "This may take 2-3 minutes..."
    docker exec plagiarism-backend python scripts/seed_corpus_matched.py --num-docs 3000
    
    echo -e "\n${YELLOW}🔄 Syncing corpus to Redis...${NC}"
    docker exec plagiarism-backend python scripts/seed_corpus_matched.py --sync-only
    
    echo -e "\n${YELLOW}🔄 Restarting backend to load corpus...${NC}"
    docker restart plagiarism-backend
    sleep 5
fi

# Step 5: Show status
echo -e "\n${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ PlagiarismGuard is running!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "🌐 Frontend:       ${BLUE}http://localhost:3000${NC}"
echo -e "🔌 Backend API:    ${BLUE}http://localhost:8000${NC}"
echo -e "📊 API Docs:       ${BLUE}http://localhost:8000/docs${NC}"
echo -e "🗄️  MinIO Console:  ${BLUE}http://localhost:9001${NC} (minioadmin/minioadmin)"
echo ""
echo -e "${YELLOW}Commands:${NC}"
echo "  docker-compose logs -f           # View logs"
echo "  docker-compose down              # Stop all services"
echo "  docker-compose ps                # Check status"
echo "  ./docker-start.sh --init-corpus  # Generate corpus"
echo ""
