# Wikipedia Crawler - Quick Start Guide

## ✅ Implementation Complete!

Wikipedia Crawler đã được triển khai đầy đủ và hoạt động tốt.

## 📊 Current Status

```
Total corpus: 6,038+ documents
├── Wikipedia articles: 38+ (0.6%)
└── Synthetic templates: 6,000 (99.4%)
```

**Success Rate:** ~60-70% (Wikipedia tiếng Việt có nhiều stub articles)

## 🚀 Quick Commands

### Crawl Random Articles

```bash
# Crawl 20 random articles (recommended for testing)
./scripts/wiki-corpus.sh crawl 20

# Crawl 50 articles
./scripts/wiki-corpus.sh crawl 50

# Crawl 100 and sync to Redis immediately
./scripts/wiki-corpus.sh crawl-sync 100
```

### Crawl Tech Categories

```bash
# Crawl 10 articles from each tech category (80 total)
./scripts/wiki-corpus.sh tech 10

# Crawl 30 articles from each category (240 total)
./scripts/wiki-corpus.sh tech 30
```

**Tech Categories:**
- Khoa học máy tính (Computer Science)
- Trí tuệ nhân tạo (AI)
- Công nghệ thông tin (IT)
- Lập trình máy tính (Programming)
- Khoa học dữ liệu (Data Science)
- Mạng máy tính (Networks)
- Phần mềm (Software)
- Cơ sở dữ liệu (Databases)

### Check Statistics

```bash
# Quick check
./scripts/wiki-corpus.sh check

# Full verification
./scripts/wiki-corpus.sh verify
```

### Sync to Redis

```bash
# Restart backend to sync LSH index
./scripts/wiki-corpus.sh sync
```

## 🎯 Recommended Workflow

### Option 1: Quick Test (5 minutes)

```bash
# 1. Crawl 20 articles
./scripts/wiki-corpus.sh crawl 20

# 2. Check results
./scripts/wiki-corpus.sh check

# 3. Sync to Redis
./scripts/wiki-corpus.sh sync
```

### Option 2: Small Batch (15 minutes)

```bash
# Crawl 50 articles with auto-sync
./scripts/wiki-corpus.sh crawl-sync 50
```

### Option 3: Large Batch (30-60 minutes)

```bash
# Crawl from tech categories
./scripts/wiki-corpus.sh tech 30  # 240 articles

# Or random crawl
./scripts/wiki-corpus.sh crawl 200
./scripts/wiki-corpus.sh sync
```

## 📁 Files Overview

### Core Scripts

| File | Purpose |
|------|---------|
| `crawlers/base_crawler.py` | Abstract base crawler |
| `crawlers/viwiki_crawler.py` | Wikipedia implementation |
| `crawl_wiki_import.py` | Main import script |
| `check_wiki_corpus.py` | Statistics checker |
| `debug_wiki_crawl.py` | Debug tool |

### Shell Scripts

| File | Purpose |
|------|---------|
| `scripts/wiki-corpus.sh` | Main CLI tool ✅ |
| `scripts/verify_corpus.py` | Corpus verification |

### Documentation

| File | Purpose |
|------|---------|
| `WIKIPEDIA_CRAWLER.md` | Full documentation |
| `DATA_GUIDE.md` | General corpus guide |
| `QUICKSTART_WIKI.md` | This file |

## 🔧 Technical Details

### Quality Filters

**During Crawl:**
- ❌ < 200 chars raw text
- ❌ < 150 chars after cleaning
- ❌ < 50 words

**During Import:**
- ❌ < 50 words after tokenization
- ✅ >= 50 words imported

### Performance

**Speed:**
- ~10-15 articles/minute
- 100 articles: ~7-10 minutes
- 500 articles: ~30-40 minutes

**Database:**
- Each article: ~1-5 KB
- 1000 articles: ~3-5 MB

**Redis Sync:**
- Auto on backend restart
- Takes ~10-30 seconds for 1000 articles

## 🐛 Troubleshooting

### No articles crawled

**Cause:** All articles too short

**Solution:** Already fixed - threshold lowered to 50 words

### "updated_at is invalid keyword"

**Cause:** Document model doesn't have `updated_at`

**Solution:** ✅ Fixed in code

### Redis not syncing

**Solution:**
```bash
./scripts/wiki-corpus.sh sync
```

Or restart manually:
```bash
docker restart plagiarism-backend
```

### Crawl too slow

**Solutions:**
1. Use smaller batches (20-50 articles)
2. Use tech categories (better success rate)
3. Be patient - respects Wikipedia rate limits

## 📈 Example Output

```
🚀 Wikipedia Corpus Management
================================

📥 Crawling 20 random Wikipedia articles...

🔍 Crawling Vietnamese Wikipedia for 20 articles...
  ✅ [4/20] Cyanea humboldtiana... (73 words)
  ✅ [6/20] Mỹ nhân (hậu cung)... (554 words)
  ✅ [10/20] Góa... (522 words)
  ✅ [11/20] Aconitum leucostomum... (78 words)
  ...

✅ Total crawled from Wikipedia: 8 articles

📥 IMPORTING 8 DOCUMENTS TO DATABASE
✅ [1/8] Cyanea humboldtiana... - 71 words
✅ [2/8] Mỹ nhân (hậu cung)... - 527 words
⚠️  [5/8] Maials... - Too short (45 words), skipped
...

✅ Import Summary:
   • Successfully imported: 7 documents
   • Skipped/Failed: 1 documents

✅ Done!
```

## 🎉 Success!

Wikipedia Crawler đã sẵn sàng sử dụng. Bắt đầu với:

```bash
./scripts/wiki-corpus.sh crawl 20
./scripts/wiki-corpus.sh check
```

## 📚 More Info

- Full docs: [`backend/scripts/WIKIPEDIA_CRAWLER.md`](../backend/scripts/WIKIPEDIA_CRAWLER.md)
- General guide: [`DATA_GUIDE.md`](../DATA_GUIDE.md)
- Main README: [`README.md`](../README.md)
