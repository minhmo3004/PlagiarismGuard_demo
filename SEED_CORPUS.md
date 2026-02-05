# 📚 Hướng Dẫn Seed Corpus - PlagiarismGuard

## Yêu Cầu
- Docker & Docker Compose đã cài đặt
- Git (để clone repo)

---

## 🚀 Cách 1: Dùng Script Setup (Khuyến Nghị)

### Quick Start
```bash
# Clone repo (nếu chưa có)
git clone <your-repo-url>
cd PlagiarismGuard_demo

# Tạo file .env từ template
cp .env.example .env

# Khởi động Docker
docker-compose up -d

# Seed corpus từ 3 nguồn (Synthetic + Wikipedia + ArXiv)
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py
```

### Các Tùy Chọn Setup

| Lệnh | Số docs | Mô tả |
|------|---------|-------|
| `python scripts/seed_corpus_matched.py --quick` | ~660 | Test nhanh (200 synthetic + 300 wiki + 160 arxiv) |
| `python scripts/seed_corpus_matched.py` | ~3,600 | Mặc định (2000 synthetic + 1000 wiki + 600 arxiv) |
| `python scripts/seed_corpus_matched.py --full` | ~6,200 | Đầy đủ (3000 synthetic + 2000 wiki + 1200 arxiv) |

**Lưu ý:** Chạy trong Docker container:
```bash
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --quick
```

### Tùy Chỉnh Từng Nguồn
```bash
# Chỉ seed synthetic 500 docs
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --synthetic 500

# Chỉ crawl Wikipedia 200 bài
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --wiki 200

# Chỉ crawl ArXiv AI + ML
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --arxiv-ai 100 --arxiv-ml 100

# Kết hợp tùy ý + sync MinIO (để xem file trong giao diện)
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --synthetic 1000 --wiki 500 --sync-minio
```

### Script sẽ tự động:
1. ✅ Seed synthetic corpus từ templates
2. ✅ Crawl Wikipedia tiếng Việt  
3. ✅ Crawl ArXiv papers (AI + ML)
4. ✅ Sync corpus vào Redis LSH index
5. ✅ Upload files lên MinIO (nếu `--sync-minio`)

**Sau khi seed xong, restart backend:**
```bash
docker restart plagiarism-backend
```

---

## 🔧 Cách 2: Setup Thủ Công (Từng Bước)

### Bước 1: Tạo file .env
```bash
cp .env.example .env
# Chỉnh sửa .env nếu cần (thay đổi ports, credentials...)
```

### Bước 2: Khởi động Docker
```bash
docker-compose up -d
```

### Bước 3: Chờ services khởi động (~30 giây)
```bash
# Kiểm tra trạng thái
docker ps --format "table {{.Names}}\t{{.Status}}"

# Chờ đến khi thấy "healthy" cho postgres, redis, minio
```

### Bước 4: Seed corpus vào PostgreSQL
```bash
# Seed 3000 tài liệu (mất ~2-3 phút)
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --num-docs 3000

# Hoặc seed ít hơn để test nhanh
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --num-docs 100
```

### Bước 5: Sync corpus từ PostgreSQL vào Redis
```bash

# sync cả Redis + MinIO
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --sync-only --sync-minio
```

### Bước 6: Restart backend để load corpus vào memory
```bash
docker restart plagiarism-backend

# Đợi 10 giây rồi kiểm tra log
docker logs plagiarism-backend --tail 20
# Phải thấy: "✅ Loaded XXXX documents into LSH index"
```

### Bước 7: Kiểm tra
```bash
# Test API
curl -s -X POST "http://localhost:8000/api/v1/plagiarism/check" \
  -F "file=@docs_test/test_plagiarized.txt" | python3 -m json.tool

# corpus_size phải > 0
```

---

## 🌐 Crawl Thêm Dữ Liệu Thủ Công

Nếu muốn crawl thêm sau khi đã setup:

### Crawl Wikipedia tiếng Việt
```bash
# Crawl 100 bài từ Wikipedia tiếng Việt
docker exec -it plagiarism-backend python scripts/crawl_wiki_import.py --random 100

# Crawl từ các category công nghệ
docker exec -it plagiarism-backend python scripts/crawl_wiki_import.py --tech-categories 30
```

### Crawl ArXiv (bài nghiên cứu tiếng Anh)
```bash
# Crawl 50 bài AI
docker exec -it plagiarism-backend python scripts/crawl_arxiv_import.py --ai 50

# Crawl 50 bài Machine Learning
docker exec -it plagiarism-backend python scripts/crawl_arxiv_import.py --ml 50
```

### Sau khi crawl xong, sync lại Redis
```bash
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --sync-only --sync-minio
docker restart plagiarism-backend
```

---

## 👀 Xem Corpus Trên MinIO

Truy cập MinIO Console:
- **URL:** http://localhost:9001
- **Username:** minioadmin
- **Password:** minioadmin

Sau khi đăng nhập:
1. Click **Object Browser** (sidebar trái)
2. Chọn bucket **`plagiarism-corpus`**
3. Browse theo năm: `corpus/2024/`, `corpus/2023/`...
4. Click vào file `.txt` để xem nội dung

---

## 📊 Tùy Chọn Seed Synthetic

| Lệnh | Số tài liệu | Thời gian |
|------|-------------|-----------|
| `--num-docs 100` | 100 | ~20 giây |
| `--num-docs 1000` | 1,000 | ~1 phút |
| `--num-docs 3000` | 3,000 | ~3 phút |

---

## 🌐 Truy Cập Ứng Dụng

| Service | URL | Mô tả |
|---------|-----|-------|
| Frontend | http://localhost:3000 | Giao diện người dùng |
| API Docs | http://localhost:8000/docs | Swagger API |
| MinIO | http://localhost:9001 | File storage (minioadmin/minioadmin) |

---

## ❓ Xử Lý Lỗi

### Lỗi: Backend không kết nối được Redis
```bash
# Kiểm tra Redis container
docker logs plagiarism-redis

# Restart nếu cần
docker restart plagiarism-redis plagiarism-backend
```

### Lỗi: corpus_size = 0 hoặc "Loaded 0 documents"
```bash
# Kiểm tra số documents trong PostgreSQL
docker exec -it plagiarism-backend python -c "
from app.db.database import SessionLocal
from app.db.models import Document
db = SessionLocal()
count = db.query(Document).filter(Document.is_corpus == 1).count()
print(f'Corpus trong PostgreSQL: {count} documents')
db.close()
"

# Nếu có documents nhưng chưa sync Redis, chạy sync
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --sync-only

# Restart backend
docker restart plagiarism-backend
```

### Lỗi: Container không start
```bash
# Xem logs để debug
docker logs plagiarism-backend
docker logs plagiarism-frontend
```

### Lỗi: Duplicate key khi crawl
Script đã tự động skip duplicate, không cần lo lắng. Xem log để biết số docs thực tế được import.

---

## 🔄 Reset Toàn Bộ

Nếu muốn xóa sạch và bắt đầu lại:
```bash
# Dừng và xóa containers + volumes
docker-compose down -v

# Khởi động lại
docker-compose up -d

# Seed lại corpus (dùng script setup)
./scripts/setup-corpus.sh

# Hoặc seed thủ công
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --num-docs 3000
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --sync-only
docker restart plagiarism-backend
```

---

## ✅ Kiểm Tra Thành Công

Khi setup xong, bạn sẽ thấy output như sau:
```
============================================================
✅ CORPUS SETUP COMPLETE
   Synthetic: 2000 docs
   Wikipedia: 1000 docs  
   ArXiv AI: 300 docs
   ArXiv ML: 300 docs
   Synced to Redis: ✅
   MinIO upload: ❌ (skip)
============================================================
```

Khi restart backend:
```
✅ Loaded 3600 documents into LSH index
```

Và khi gọi API check, `corpus_size` phải > 0.

---

## 📚 Nguồn Dữ Liệu Corpus

| Nguồn | Ngôn ngữ | Mô tả |
|-------|----------|-------|
| 🔹 **Synthetic** | Tiếng Việt | Tạo từ templates + `docs_test/` |
| 🔹 **Wikipedia** | Tiếng Việt | Crawl từ Wikipedia tiếng Việt |
| 🔹 **ArXiv** | Tiếng Anh | Crawl papers AI/ML từ ArXiv |

**Scripts có sẵn:**
| Script | Mô tả |
|--------|-------|
| `seed_corpus_matched.py` | **Script chính** - seed từ 3 nguồn với options |
| `crawl_wiki_import.py` | Crawl Wikipedia tiếng Việt (standalone) |
| `crawl_arxiv_import.py` | Crawl ArXiv papers (standalone) |

**Tất cả options của seed_corpus_matched.py:**
```
--quick              Quick setup (~660 docs)
--full               Full setup (~6,200 docs)
--synthetic N        Số synthetic docs
--wiki N             Số Wikipedia articles
--arxiv-ai N         Số ArXiv AI papers
--arxiv-ml N         Số ArXiv ML papers
--sync-only          Chỉ sync Redis (không seed)
--sync-minio         Upload files lên MinIO
--num-docs N         (Legacy) Chỉ seed synthetic
```

**Workflow nạp dữ liệu:**
```
Seed/Crawl → PostgreSQL → sync-only → Redis → restart → LSH Index
```

