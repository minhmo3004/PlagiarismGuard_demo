#!/bin/bash
# View Corpus Database - PlagiarismGuard

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         PlagiarismGuard - Corpus Database Viewer              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# PostgreSQL Statistics
echo "📊 PostgreSQL Corpus Statistics:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker exec plagiarism-postgres psql -U postgres -d plagiarism -t -c "
SELECT 
    '  Total docs: ' || COUNT(*) || E'\n' ||
    '  Avg words: ' || ROUND(AVG(word_count)) || E'\n' ||
    '  Min words: ' || MIN(word_count) || E'\n' ||
    '  Max words: ' || MAX(word_count) || E'\n' ||
    '  Universities: ' || COUNT(DISTINCT university) || E'\n' ||
    '  Authors: ' || COUNT(DISTINCT author)
FROM documents WHERE status = 'indexed';
"

echo ""
echo "🏛️  Top 5 Universities:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker exec plagiarism-postgres psql -U postgres -d plagiarism -c "
SELECT 
    LEFT(university, 40) as university, 
    COUNT(*) as docs 
FROM documents 
WHERE status = 'indexed' 
GROUP BY university 
ORDER BY docs DESC 
LIMIT 5;
" | grep -v "rows)"

echo ""
echo "📅 Distribution by Year:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker exec plagiarism-postgres psql -U postgres -d plagiarism -c "
SELECT year, COUNT(*) as docs 
FROM documents 
WHERE status = 'indexed' 
GROUP BY year 
ORDER BY year DESC;
" | grep -v "rows)"

echo ""
echo "🔴 Redis LSH Index:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker exec plagiarism-backend python -c "
import redis
from app.config import settings
r = redis.from_url(settings.REDIS_URL, decode_responses=True)
sig_count = len(r.keys('doc:sig:*'))
meta_count = len(r.keys('doc:meta:*'))
print(f'  Signatures: {sig_count}')
print(f'  Metadata: {meta_count}')
"

echo ""
echo "📄 Sample Documents (latest 5):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker exec plagiarism-postgres psql -U postgres -d plagiarism -c "
SELECT 
    LEFT(title, 45) as title,
    author,
    word_count,
    year
FROM documents 
WHERE status = 'indexed'
ORDER BY created_at DESC
LIMIT 5;
" | grep -v "rows)"

echo ""
echo "╚════════════════════════════════════════════════════════════════╝"
