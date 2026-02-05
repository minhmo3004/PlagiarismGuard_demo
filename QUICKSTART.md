# PlagiarismGuard 2.0 - Quick Start Guide

## 🚀 Cách sử dụng

### Bước 1: Khởi động Docker
```bash
docker-compose up -d
```

### Bước 2: Seed Corpus (3 nguồn)
```bash
# Setup nhanh (~660 docs)
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --quick

# HOẶC Setup mặc định (~3,600 docs)
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py

# HOẶC Setup đầy đủ (~6,200 docs)
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --full
```
⏱️ **Thời gian:** 5-15 phút tùy lựa chọn

Script sẽ tự động:
- ✅ Seed synthetic corpus (tiếng Việt)
- ✅ Crawl Wikipedia (tiếng Việt)  
- ✅ Crawl ArXiv (AI/ML papers)
- ✅ Sync vào Redis LSH index

### Bước 3: Restart backend & Mở ứng dụng
```bash
docker restart plagiarism-backend
```
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000

---

## 🔧 Tùy Chỉnh Corpus

```bash
# Chỉ seed synthetic
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --synthetic 1000

# Chỉ crawl Wikipedia
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --wiki 500

# Kết hợp + upload MinIO (để xem files)
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --synthetic 500 --wiki 300 --sync-minio
```

---

## 🌐 Crawl thêm dữ liệu (Sau khi setup)

```bash
# Crawl Wikipedia tiếng Việt
docker exec -it plagiarism-backend python scripts/crawl_wiki_import.py --random 100

# Crawl ArXiv papers
docker exec -it plagiarism-backend python scripts/crawl_arxiv_import.py --ai 50

# Sau khi crawl, sync lại Redis
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --sync-only
docker restart plagiarism-backend
```

---

## 📁 File test mẫu

Trong folder `docs_test/`:
- `do_an_AI_y_te.txt` - AI trong Y tế (423 từ)
- `luan_van_blockchain.txt` - Blockchain (428 từ)
- `do_an_chatbot_nlp.txt` - Chatbot NLP (401 từ)
- `khoa_luan_an_ninh_mang.txt` - An ninh mạng (401 từ)
- `do_an_face_recognition.txt` - Face Recognition (407 từ)

Upload các file này để test phát hiện đạo văn!

---

## 🔗 URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| MinIO Console | http://localhost:9001 (minioadmin/minioadmin) |

---

## 📊 Check Corpus

```bash
# Kiểm tra số documents trong PostgreSQL
docker exec -it plagiarism-backend python -c "
from app.db.database import SessionLocal
from app.db.models import Document
db = SessionLocal()
count = db.query(Document).filter(Document.is_corpus == 1).count()
print(f'Corpus: {count} documents')
db.close()
"
```

---

## 🐛 Troubleshooting

### corpus_size = 0 hoặc "Loaded 0 documents"
```bash
# Sync corpus từ PostgreSQL vào Redis
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --sync-only
docker restart plagiarism-backend
```

### Redis không kết nối được
```bash
docker restart plagiarism-redis plagiarism-backend
```

### Xem logs
```bash
docker logs plagiarism-backend --tail 50
docker logs plagiarism-frontend --tail 50
```

### Reset toàn bộ
```bash
docker-compose down -v
docker-compose up -d
# Rồi seed lại từ Bước 2
```
