#!/bin/bash
# ============================================================
# SETUP CORPUS - Chạy 1 lần khi deploy lên máy mới
# Crawl 1000 tài liệu từ Wikipedia + ArXiv
# ============================================================

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║       PLAGIARISM GUARD - CORPUS SETUP                    ║"
echo "║       Crawl 1000 tài liệu từ Wikipedia + ArXiv           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${YELLOW}❌ Docker không chạy. Vui lòng start Docker trước.${NC}"
    exit 1
fi

# Check backend container
if ! docker ps | grep -q plagiarism-backend; then
    echo -e "${YELLOW}❌ Backend container không chạy.${NC}"
    echo "Chạy: docker-compose up -d"
    exit 1
fi

echo -e "${BLUE}📊 Kiểm tra corpus hiện tại...${NC}"
docker exec plagiarism-backend python scripts/check_wiki_corpus.py

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}📥 PHASE 1: Crawl Vietnamese Wikipedia (500 articles)${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Crawl 500 random Wikipedia articles
echo -e "${BLUE}🔍 Crawling 500 random Vietnamese Wikipedia articles...${NC}"
docker exec plagiarism-backend python scripts/crawl_wiki_import.py --random 500

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}📥 PHASE 2: Crawl Wikipedia Tech Categories (300 articles)${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Crawl tech categories (8 categories x ~40 each = ~300 articles)
echo -e "${BLUE}🔍 Crawling tech categories (AI, ML, IT, Security...)${NC}"
docker exec plagiarism-backend python scripts/crawl_wiki_import.py --tech-categories 40

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}📥 PHASE 3: Crawl ArXiv Papers (200 papers)${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Crawl ArXiv multi-category (5 categories x 40 = 200 papers)
echo -e "${BLUE}🔍 Crawling ArXiv papers (AI, ML, CV, NLP, Security)...${NC}"
docker exec plagiarism-backend python scripts/crawl_arxiv_import.py --multi-category 40

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🔄 PHASE 4: Sync to Redis LSH Index${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${BLUE}🔄 Restarting backend to sync Redis...${NC}"
docker restart plagiarism-backend

echo -e "${YELLOW}⏳ Waiting 15 seconds for backend to start...${NC}"
sleep 15

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ SETUP COMPLETE!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Final check
echo -e "${BLUE}📊 Corpus statistics after setup:${NC}"
docker exec plagiarism-backend python scripts/check_wiki_corpus.py

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ Corpus đã sẵn sàng để sử dụng!                       ║${NC}"
echo -e "${GREEN}║  🌐 Frontend: http://localhost:3000                      ║${NC}"
echo -e "${GREEN}║  🔌 Backend API: http://localhost:8000                   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
