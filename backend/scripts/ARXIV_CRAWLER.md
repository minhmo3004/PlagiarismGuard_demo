# ArXiv Academic Paper Crawler

## Overview

ArXiv crawler thu thập papers khoa học từ ArXiv.org - kho lưu trữ preprint mở lớn nhất thế giới.

## Why ArXiv?

✅ **Legal & Safe:**
- Open access repository
- Official API available
- No copyright issues
- Encouraged for research use

✅ **High Quality:**
- Peer-reviewed preprints
- Latest research papers
- Top universities & labs
- CS, AI, ML, Physics, Math

✅ **Relevant Content:**
- Computer Science papers (cs.AI, cs.LG, cs.CV, cs.CL)
- Machine Learning research
- Natural Language Processing
- Security & Cryptography

## Features

- ✅ Search by category (AI, ML, CV, NLP, Security)
- ✅ Filter Vietnamese-related papers
- ✅ Official XML API (safe & legal)
- ✅ Rate limiting (3s delay)
- ✅ Auto-import to database
- ✅ English content (good for multilingual corpus)

## Categories

**Available ArXiv Categories:**

```python
'cs.AI'  # Artificial Intelligence
'cs.LG'  # Machine Learning
'cs.CV'  # Computer Vision
'cs.CL'  # Computation and Language (NLP)
'cs.CR'  # Cryptography and Security
'cs.DB'  # Databases
'cs.DC'  # Distributed Computing
'cs.DS'  # Data Structures and Algorithms
```

## Usage

### 1. Crawl AI Papers

```bash
# Crawl 50 AI papers
docker exec plagiarism-backend python scripts/crawl_arxiv_import.py --ai 50

# Crawl and sync to Redis
docker exec plagiarism-backend python scripts/crawl_arxiv_import.py --ai 100 --sync-redis
```

### 2. Crawl Machine Learning Papers

```bash
# Crawl 30 ML papers
docker exec plagiarism-backend python scripts/crawl_arxiv_import.py --ml 30
```

### 3. Crawl Computer Vision Papers

```bash
# Crawl 20 CV papers
docker exec plagiarism-backend python scripts/crawl_arxiv_import.py --cv 20
```

### 4. Crawl NLP Papers

```bash
# Crawl 40 NLP papers
docker exec plagiarism-backend python scripts/crawl_arxiv_import.py --nlp 40
```

### 5. Crawl Vietnamese-related Papers

```bash
# Search papers mentioning Vietnam/Vietnamese
docker exec plagiarism-backend python scripts/crawl_arxiv_import.py --vietnamese 50
```

### 6. Crawl Multiple Categories

```bash
# Crawl 20 papers from each category (AI, ML, CV, NLP, Security)
docker exec plagiarism-backend python scripts/crawl_arxiv_import.py --multi-category 20
```

### 7. Sync After Crawling

```bash
# Sync corpus to Redis after crawling
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --sync-only

# Restart backend to load into memory
docker restart plagiarism-backend
```

## How It Works

### API Request

```python
GET http://export.arxiv.org/api/query

Parameters:
  search_query: cat:cs.AI
  start: 0
  max_results: 50
  sortBy: relevance
  sortOrder: descending
```

### Response Processing

```xml
<entry>
  <id>http://arxiv.org/abs/2301.12345</id>
  <title>Deep Learning for NLP</title>
  <author><name>John Doe</name></author>
  <author><name>Jane Smith</name></author>
  <summary>This paper presents...</summary>
  <category term="cs.AI"/>
  <published>2023-01-15</published>
</entry>
```

### Import to Database

```python
Document(
    title="Deep Learning for NLP",
    author="John Doe, Jane Smith",
    university="ArXiv",
    extracted_text="Title + Abstract",
    word_count=350,
    language='en',
    extraction_method='arxiv_crawler',
    is_corpus=1
)
```

## Output Example

```
🚀 Starting ArXiv Crawler...
Mode: AI papers (cs.AI, n=30)

🔍 Searching ArXiv:  in cs.AI
  ✅ [1] Attention Is All You Need... (287 words)
  ✅ [2] BERT: Pre-training of Deep Bidirectional... (445 words)
  ✅ [3] GPT-3: Language Models are Few-Shot Learners... (678 words)
  ✅ [4] ResNet: Deep Residual Learning... (398 words)
  ...

✅ Total crawled from ArXiv: 28 papers

======================================================================
📥 IMPORTING 28 DOCUMENTS TO DATABASE
======================================================================

✅ [1/28] Attention Is All You Need... - 287 words
✅ [2/28] BERT: Pre-training... - 445 words
...

======================================================================
✅ Import Summary:
   • Successfully imported: 28 documents
   • Skipped/Failed: 0 documents
   • Total processed: 28 documents
======================================================================
```

## Quality Filters

**Crawl Stage:**
- ✅ Only papers with abstracts
- ✅ Valid XML entries
- ❌ Skip entries without title/summary

**Import Stage:**
- ❌ Skip if < 100 words (too short)
- ✅ Include papers >= 100 words

**Result:**
- Success rate: ~95% (high quality source)
- Average word count: 250-500 words (title + abstract)
- Language: English (good for multilingual detection)

## Rate Limiting

**Delay**: 3.0 seconds between requests  
**User-Agent**: `PlagiarismGuard/2.0 (Educational Research)`  
**Compliance**: Follows ArXiv API guidelines

**ArXiv API Guidelines:**
- ✅ Use official API endpoint
- ✅ Include descriptive User-Agent
- ✅ Rate limit to 1 request per 3 seconds
- ✅ Respect server load

## Advantages Over University Crawling

| Feature | ArXiv | University Sites |
|---------|-------|------------------|
| **Legal** | ✅ Official API | ⚠️ May violate ToS |
| **Copyright** | ✅ Open Access | ⚠️ Restricted |
| **API** | ✅ XML API | ❌ No API usually |
| **Quality** | ✅ High | ✅ High |
| **Vietnamese** | ⚠️ Limited | ✅ Many |
| **Rate Limit** | ✅ Clear rules | ⚠️ Unclear |
| **Success Rate** | ✅ 95%+ | ⚠️ 30-50% |

## Verification

### Check ArXiv Papers Count

```bash
docker exec plagiarism-backend python -c "
import sys
sys.path.insert(0, '/app')
from app.db.database import SessionLocal
from app.db.models import Document
from sqlalchemy import func

db = SessionLocal()

arxiv = db.query(func.count(Document.id)).filter(
    Document.extraction_method == 'arxiv_crawler'
).scalar()
print(f'ArXiv papers: {arxiv}')

db.close()
"
```

### View Recent ArXiv Papers

```bash
docker exec plagiarism-backend python -c "
import sys
sys.path.insert(0, '/app')
from app.db.database import SessionLocal
from app.db.models import Document

db = SessionLocal()

papers = db.query(Document.title, Document.author, Document.word_count).filter(
    Document.extraction_method == 'arxiv_crawler'
).order_by(Document.created_at.desc()).limit(10).all()

print('\nRecent ArXiv Papers:')
for title, author, wc in papers:
    print(f'  • {title[:50]}... by {author[:30]} ({wc} words)')

db.close()
"
```

## Performance

**Crawl Speed:**
- ~20 papers/minute (3s delay)
- 100 papers: ~5 minutes
- 500 papers: ~25 minutes

**Success Rate:**
- ArXiv API: 95-98% (very reliable)
- Import to DB: 98%+ (high quality abstracts)

**Database Impact:**
- Each paper: ~2-5 KB (title + abstract)
- 1000 papers: ~3-5 MB total

## Best Practices

### 1. Start with Specific Categories

```bash
# More relevant than random crawl
docker exec -it plagiarism-backend python scripts/crawl_arxiv_import.py --ai 50
docker exec -it plagiarism-backend python scripts/crawl_arxiv_import.py --ml 50
```

### 2. Use Multi-category for Diversity

```bash
# 10 papers from each category (50 total)
docker exec -it plagiarism-backend python scripts/crawl_arxiv_import.py --multi-category 10
```

### 3. Combine with Wikipedia

```bash
# Wikipedia for Vietnamese content
docker exec -it plagiarism-backend python scripts/crawl_wiki_import.py --random 100

# ArXiv for English academic content
docker exec -it plagiarism-backend python scripts/crawl_arxiv_import.py --ai 50

# Sync to Redis
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --sync-only
docker restart plagiarism-backend
```

### 4. Sync After Large Imports

```bash
# After importing many documents
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --sync-only
docker restart plagiarism-backend
```

## Troubleshooting

### Problem: No papers returned

**Cause**: Network issues or ArXiv server down

**Solution**:
```bash
# Test ArXiv API directly
curl "http://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=1"
```

### Problem: Papers too short

**Cause**: Some papers have brief abstracts

**Solution**: Filter already implemented (100 words minimum)

### Problem: Language mismatch

**Note**: ArXiv is mostly English, which is GOOD for:
- Multilingual plagiarism detection
- Detecting translation plagiarism
- Diverse corpus

## Google Scholar (Future)

⚠️ **Not implemented yet** - requires special handling:

**Challenges:**
- No official API
- Strict rate limiting
- IP blocking risk
- ToS violations

**Alternatives:**
1. Use `scholarly` Python library (careful with rate limits)
2. Use SerpAPI (paid service, $50/month)
3. Request official university API access

**For now, stick with ArXiv** - it's legal, safe, and high quality.

## License & Attribution

All ArXiv content is under various open licenses (usually CC BY).

**Attribution**: Authors listed in paper metadata

**Compliance**: This crawler follows ArXiv API Terms of Service.

## Documentation

- [ArXiv API User Manual](https://arxiv.org/help/api/user-manual)
- [ArXiv API TOS](https://arxiv.org/help/api/tou)
- [Category Taxonomy](https://arxiv.org/category_taxonomy)

## Support

For ArXiv-specific issues, check [ArXiv Help](https://arxiv.org/help).

For crawler issues, check logs:
```bash
docker logs -f plagiarism-backend
```
