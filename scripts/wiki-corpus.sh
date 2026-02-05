#!/bin/bash
# Quick script to crawl Wikipedia and check corpus

set -e

echo "🚀 Wikipedia Corpus Management"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
CMD=${1:-help}
N=${2:-100}

case $CMD in
  crawl)
    echo -e "${GREEN}📥 Crawling $N random Wikipedia articles...${NC}"
    docker exec plagiarism-backend python scripts/crawl_wiki_import.py --random $N
    ;;
    
  crawl-sync)
    echo -e "${GREEN}📥 Crawling $N articles + syncing to Redis...${NC}"
    docker exec plagiarism-backend python scripts/crawl_wiki_import.py --random $N --sync-redis
    ;;
    
  tech)
    echo -e "${GREEN}📥 Crawling $N articles from tech categories...${NC}"
    docker exec plagiarism-backend python scripts/crawl_wiki_import.py --tech-categories $N
    ;;
    
  check)
    echo -e "${GREEN}📊 Checking corpus statistics...${NC}"
    docker exec plagiarism-backend python scripts/check_wiki_corpus.py
    ;;
    
  verify)
    echo -e "${GREEN}✅ Verifying corpus requirements...${NC}"
    docker exec plagiarism-backend python scripts/verify_corpus.py
    ;;
    
  sync)
    echo -e "${YELLOW}🔄 Restarting backend to sync Redis...${NC}"
    docker restart plagiarism-backend
    echo -e "${GREEN}✅ Done! Wait 10 seconds for backend to start...${NC}"
    ;;
    
  arxiv-ai)
    echo -e "${GREEN}📥 Crawling $N ArXiv AI papers...${NC}"
    docker exec plagiarism-backend python scripts/crawl_arxiv_import.py --ai $N
    ;;
    
  arxiv-ml)
    echo -e "${GREEN}📥 Crawling $N ArXiv ML papers...${NC}"
    docker exec plagiarism-backend python scripts/crawl_arxiv_import.py --ml $N
    ;;
    
  arxiv-multi)
    echo -e "${GREEN}📥 Crawling $N papers from each ArXiv category...${NC}"
    docker exec plagiarism-backend python scripts/crawl_arxiv_import.py --multi-category $N
    ;;
    
  help|*)
    echo "Usage: $0 <command> [N]"
    echo ""
    echo "Wikipedia Commands:"
    echo "  crawl [N]      - Crawl N random Wikipedia articles (default: 100)"
    echo "  crawl-sync [N] - Crawl N articles and sync to Redis immediately"
    echo "  tech [N]       - Crawl N articles from each tech category"
    echo ""
    echo "ArXiv Commands:"
    echo "  arxiv-ai [N]   - Crawl N ArXiv AI papers (cs.AI)"
    echo "  arxiv-ml [N]   - Crawl N ArXiv ML papers (cs.LG)"
    echo "  arxiv-multi [N]- Crawl N from each category (AI, ML, CV, NLP, Security)"
    echo ""
    echo "General Commands:"
    echo "  check          - Check corpus and Wikipedia statistics"
    echo "  verify         - Verify corpus meets requirements"
    echo "  sync           - Restart backend to sync Redis LSH index"
    echo "  help           - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 crawl 50          # Crawl 50 random Wiki articles"
    echo "  $0 arxiv-ai 30       # Crawl 30 AI papers from ArXiv"
    echo "  $0 arxiv-multi 10    # Crawl 10 from each ArXiv category"
    echo "  $0 check             # Check statistics"
    echo ""
    ;;
esac
