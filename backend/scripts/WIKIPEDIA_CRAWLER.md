# Wikipedia Crawler Documentation

## Overview

Wikipedia Crawler tự động thu thập nội dung tiếng Việt từ Wikipedia và nhập vào corpus database để phát hiện đạo văn.

## Features

✅ **Crawl Random Articles**: Thu thập bài viết ngẫu nhiên  
✅ **Category-based Crawling**: Thu thập theo chủ đề (Khoa học máy tính, AI, IT...)  
✅ **Text Cleaning**: Loại bỏ headers, citations, formatting  
✅ **Quality Filtering**: Chỉ giữ bài viết đủ dài (>50 words)  
✅ **Auto Import**: Tự động import vào PostgreSQL  
✅ **Redis Sync**: Đồng bộ LSH index để detect plagiarism  

## Architecture

```
┌─────────────────┐
│  vi.wikipedia   │ MediaWiki API
│  (vi.wikipedia  │ ────────────┐
│   .org)         │             │
└─────────────────┘             │
                                ▼
                    ┌───────────────────────┐
                    │  ViWikiCrawler        │
                    │  ─────────────────    │
                    │  • Get random pages   │
                    │  • Extract content    │
                    │  • Clean text         │
                    │  • Filter quality     │
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  crawl_wiki_import.py │
                    │  ─────────────────    │
                    │  • Normalize text     │
                    │  • Tokenize (VnCoreNLP│
                    │  • Import to DB       │
                    └───────────────────────┘
                                │
                    ┌───────────┴──────────┐
                    ▼                      ▼
        ┌──────────────────┐   ┌──────────────────┐
        │   PostgreSQL     │   │   Redis LSH      │
        │   (documents)    │   │   (signatures)   │
        └──────────────────┘   └──────────────────┘
```

## Usage

### 1. Crawl Random Articles

```bash
# Crawl 100 random Vietnamese Wikipedia articles
docker exec plagiarism-backend python scripts/crawl_wiki_import.py --random 100

# Crawl and sync to Redis immediately
docker exec plagiarism-backend python scripts/crawl_wiki_import.py --random 100 --sync-redis
```

### 2. Crawl Tech Categories

```bash
# Crawl 20 articles from each tech category
# Categories: AI, Computer Science, IT, Programming, Data Science, Networks, Software, Databases
docker exec plagiarism-backend python scripts/crawl_wiki_import.py --tech-categories 20

# With Redis sync
docker exec plagiarism-backend python scripts/crawl_wiki_import.py --tech-categories 30 --sync-redis
```

### 3. Crawl Specific Category

```bash
# Crawl from specific Wikipedia category
docker exec plagiarism-backend python scripts/crawl_wiki_import.py \
    --category "Khoa_học_máy_tính" \
    --limit 50

# Other categories
docker exec plagiarism-backend python scripts/crawl_wiki_import.py \
    --category "Trí_tuệ_nhân_tạo" \
    --limit 50 --sync-redis
```

## How It Works

### Step 1: Crawling

1. **Random Selection**: MediaWiki API `list=random` namespace=0 (main articles)
2. **Content Extraction**: `prop=extracts` explaintext=True (plain text)
3. **Initial Filter**: Bỏ bài < 200 chars
4. **Text Cleaning**: Loại bỏ headers (==, ===), citations, language marks

### Step 2: Processing

```python
# Normalize Vietnamese text
normalized = normalize_text(raw_text)

# Tokenize using VnCoreNLP
tokens = preprocess_vietnamese(normalized)

# Count words
word_count = len(tokens)

# Filter: minimum 50 words
if word_count < 50:
    skip()
```

### Step 3: Import to Database

```python
Document(
    title="Article Title",
    author="Wikipedia Contributors",
    university="Vietnamese Wikipedia",
    original_filename="wiki_article.txt",
    file_hash_sha256=hash(content),
    word_count=word_count,
    extracted_text=content,
    is_corpus=1,  # Mark as corpus
    extraction_method='wikipedia_crawler',
    status='indexed'
)
```

### Step 4: Sync to Redis (Optional)

```bash
# Manual sync
docker restart plagiarism-backend

# Or use --sync-redis flag during crawl
```

## Quality Filters

**Crawl Stage:**
- ❌ Bỏ bài < 200 chars raw text
- ❌ Bỏ bài < 150 chars after cleaning
- ❌ Bỏ bài < 50 words

**Import Stage:**
- ❌ Bỏ bài < 50 words after tokenization
- ✅ Giữ bài >= 50 words

**Result:**
- Success rate: ~60-70% (Wikipedia tiếng Việt có nhiều stub articles)
- Average word count: 200-500 words
- Quality: Medium to High (well-structured articles)

## Tech Categories

Predefined tech categories for targeted crawling:

```python
tech_categories = [
    'Khoa_học_máy_tính',      # Computer Science
    'Trí_tuệ_nhân_tạo',       # Artificial Intelligence
    'Công_nghệ_thông_tin',    # Information Technology
    'Lập_trình_máy_tính',     # Programming
    'Khoa_học_dữ_liệu',       # Data Science
    'Mạng_máy_tính',          # Computer Networks
    'Phần_mềm',               # Software
    'Cơ_sở_dữ_liệu'           # Databases
]
```

## Rate Limiting

**Delay**: 1.5 seconds between requests  
**User-Agent**: `PlagiarismGuard/2.0 (Educational Research)`  
**Retry**: 3 attempts with exponential backoff  

**Respects Wikipedia ToS:**
- ✅ Identifies bot with proper User-Agent
- ✅ Rate-limited to avoid server load
- ✅ Uses official MediaWiki API (not scraping)

## Output Example

```
🚀 Starting Wikipedia Crawler...

🔍 Crawling Vietnamese Wikipedia for 100 articles...
Mode: Random articles (n=100)
  ✅ [1/100] Trí tuệ nhân tạo... (856 words)
  ✅ [2/100] Python (ngôn ngữ lập trình)... (1234 words)
  ✅ [3/100] Machine Learning... (678 words)
  ...
  ✅ [60/100] Blockchain... (445 words)

✅ Total crawled from Wikipedia: 60 articles

======================================================================
📥 IMPORTING 60 DOCUMENTS TO DATABASE
======================================================================

✅ [1/60] Trí tuệ nhân tạo... - 723 words
✅ [2/60] Python (ngôn ngữ lập trình)... - 1048 words
⚠️  [3/60] Stub Article... - Too short (32 words), skipped
...
✅ [58/60] Blockchain... - 389 words

======================================================================
✅ Import Summary:
   • Successfully imported: 55 documents
   • Skipped/Failed: 5 documents
   • Total processed: 60 documents
======================================================================

✅ Successfully imported 55 documents to database

⚠️  TO SYNC TO REDIS LSH INDEX:
   Run: docker restart plagiarism-backend
   Or use --sync-redis flag next time

✅ Done!
```

## Verification

### Check Corpus Size

```bash
docker exec plagiarism-backend python -c "
import sys
sys.path.insert(0, '/app')
from app.db.database import SessionLocal
from app.db.models import Document
from sqlalchemy import func

db = SessionLocal()

# Total corpus
total = db.query(func.count(Document.id)).filter(Document.is_corpus == 1).scalar()
print(f'Total corpus: {total}')

# Wikipedia articles
wiki = db.query(func.count(Document.id)).filter(
    Document.extraction_method == 'wikipedia_crawler'
).scalar()
print(f'Wikipedia articles: {wiki}')

db.close()
"
```

### View Recent Articles

```bash
docker exec plagiarism-backend python scripts/verify_corpus.py
```

## Performance

**Crawl Speed:**
- ~10-15 articles/minute (with 1.5s delay)
- 100 articles: ~7-10 minutes
- 500 articles: ~30-40 minutes

**Success Rate:**
- Random crawl: 60-70% (many stubs)
- Tech categories: 70-80% (better quality)

**Database Impact:**
- Each article: ~1-5 KB text
- 1000 articles: ~3-5 MB total

**Redis Sync:**
- Auto-sync on backend restart
- Or manual: `docker restart plagiarism-backend`
- Sync time: ~10-30 seconds for 1000 articles

## Troubleshooting

### Problem: "403 Forbidden" from Wikipedia

**Cause**: Missing or improper User-Agent header

**Solution**: Already fixed - `User-Agent: PlagiarismGuard/2.0 (Educational Research)`

### Problem: "0 articles crawled"

**Causes:**
1. Articles too short (<200 chars)
2. Network issues
3. Wikipedia API rate limiting

**Solution:**
- ✅ Threshold lowered to 200 chars
- ✅ Retry logic with backoff
- ✅ 1.5s delay between requests

### Problem: "updated_at is an invalid keyword argument"

**Cause**: Document model doesn't have `updated_at` field

**Solution**: ✅ Fixed - removed from import script

### Problem: Redis not syncing

**Solution:**
```bash
# Manual restart backend to trigger re-indexing
docker restart plagiarism-backend

# Check logs
docker logs -f plagiarism-backend
# Should see: "Loading corpus... Loaded 6xxx documents"
```

## Best Practices

### 1. Start Small

```bash
# Test with 10 articles first
docker exec plagiarism-backend python scripts/crawl_wiki_import.py --random 10
```

### 2. Gradual Expansion

```bash
# Then 50
docker exec plagiarism-backend python scripts/crawl_wiki_import.py --random 50

# Then 200
docker exec plagiarism-backend python scripts/crawl_wiki_import.py --random 200 --sync-redis
```

### 3. Use Tech Categories for Quality

```bash
# Higher success rate and better content
docker exec plagiarism-backend python scripts/crawl_wiki_import.py --tech-categories 50
```

### 4. Monitor Progress

```bash
# Run verification after import
docker exec plagiarism-backend python scripts/verify_corpus.py
```

### 5. Sync Redis After Large Imports

```bash
# After importing 500+ articles
docker restart plagiarism-backend

# Or use --sync-redis during import
```

## Files

### Core Scripts

- **`crawlers/base_crawler.py`**: Abstract base crawler class
- **`crawlers/viwiki_crawler.py`**: Vietnamese Wikipedia implementation
- **`crawl_wiki_import.py`**: Main import script with CLI

### Supporting Files

- **`verify_corpus.py`**: Check corpus statistics
- **`debug_wiki_crawl.py`**: Debug crawler issues

### Documentation

- **`WIKIPEDIA_CRAWLER.md`**: This file
- **`DATA_GUIDE.md`**: General corpus management guide

## Examples

### Quick Test (10 articles)

```bash
docker exec plagiarism-backend python scripts/crawl_wiki_import.py --random 10
```

### Small Batch (50 articles + sync)

```bash
docker exec plagiarism-backend python scripts/crawl_wiki_import.py --random 50 --sync-redis
```

### Large Batch (200 articles)

```bash
docker exec plagiarism-backend python scripts/crawl_wiki_import.py --random 200 --sync-redis
```

### Tech-focused (100 articles from 8 categories)

```bash
docker exec plagiarism-backend python scripts/crawl_wiki_import.py --tech-categories 100
```

### Specific Category (100 AI articles)

```bash
docker exec plagiarism-backend python scripts/crawl_wiki_import.py \
    --category "Trí_tuệ_nhân_tạo" \
    --limit 100 \
    --sync-redis
```

## Future Enhancements

**Planned:**
- [ ] Add more categories (Medicine, Law, History, etc.)
- [ ] Improve text cleaning (better citation removal)
- [ ] Add content deduplication
- [ ] Support for other languages (English Wikipedia)
- [ ] Parallel crawling for faster speed
- [ ] Database transaction rollback on errors

**Ideas:**
- Crawl specific lists (e.g., "List of AI algorithms")
- Prioritize featured/good articles
- Add article quality scoring
- Support for other wikis (Wiktionary, Wikiquote)

## License & Attribution

All Wikipedia content is under Creative Commons Attribution-ShareAlike 3.0 License.

**Attribution**: Wikipedia Contributors - Vietnamese Wikipedia

**Compliance**: This crawler follows Wikipedia's API terms of service.

## Support

Questions? Check [DATA_GUIDE.md](../DATA_GUIDE.md) for general corpus management.

Issues? Check logs:
```bash
docker logs -f plagiarism-backend
```
