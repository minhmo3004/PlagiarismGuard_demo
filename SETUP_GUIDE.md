# 🚀 Hướng Dẫn Cài Đặt & Chạy PlagiarismGuard 2.0

## Mục Lục
1. [Yêu Cầu Hệ Thống](#1-yêu-cầu-hệ-thống)
2. [Cài Đặt Nhanh](#2-cài-đặt-nhanh)
3. [Seed Corpus](#3-seed-corpus)
4. [Chạy Test](#4-chạy-test)
5. [Truy Cập Ứng Dụng](#5-truy-cập-ứng-dụng)
6. [Xử Lý Lỗi](#6-xử-lý-lỗi)

---

## 1. Yêu Cầu Hệ Thống

| Yêu cầu | Phiên bản |
|---------|-----------|
| Docker | >= 20.0 |
| Docker Compose | >= 2.0 |
| RAM | >= 8GB (khuyến nghị) |
| Disk | >= 5GB trống |

---

## 2. Cài Đặt Nhanh

### Bước 1: Clone Repository
```bash
git clone <your-repo-url>
cd PlagiarismGuard_demo
```

### Bước 2: Tạo File Environment
```bash
cp .env.example .env
# Chỉnh sửa .env nếu cần thay đổi ports hoặc credentials
```

### Bước 3: Khởi Động Docker
```bash
docker-compose up -d
```

### Bước 4: Seed Corpus từ 3 Nguồn
```bash
# Setup nhanh (~660 docs) - để test
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --quick

# HOẶC Setup mặc định (~3,600 docs)
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py

# HOẶC Setup đầy đủ (~6,200 docs)
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --full

# Sau khi seed xong, restart backend
docker restart plagiarism-backend
```

> ⏱️ Thời gian: 5-15 phút tùy lựa chọn

---

## 3. Seed Corpus

### 3.1. Dùng Script Seed (Khuyến Nghị)
```bash
# Seed từ 3 nguồn: Synthetic + Wikipedia + ArXiv
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py
```

Các tùy chọn:
| Lệnh | Docs | Mô tả |
|------|------|-------|
| `--quick` | ~660 | Test nhanh |
| (mặc định) | ~3,600 | Cân bằng |
| `--full` | ~6,200 | Đầy đủ |
| `--sync-minio` | - | Upload files lên MinIO |

### 3.2. Tùy Chỉnh Từng Nguồn
```bash
# Chỉ seed synthetic
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --synthetic 1000

# Chỉ crawl Wikipedia
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --wiki 500

# Kết hợp
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --synthetic 500 --wiki 300 --arxiv-ai 100

# Kèm upload MinIO (để xem file)
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --synthetic 500 --sync-minio
```

### 3.3. Crawl Riêng Từng Nguồn
```bash
# Seed synthetic docs only (legacy)
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --num-docs 3000

# Crawl Wikipedia only
docker exec -it plagiarism-backend python scripts/crawl_wiki_import.py --random 500

# Crawl ArXiv only
docker exec -it plagiarism-backend python scripts/crawl_arxiv_import.py --ai 100

# Sync vào Redis LSH index
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --sync-only

# Restart backend để load corpus
docker restart plagiarism-backend
```

### 3.4. Kiểm Tra Corpus Đã Seed
```bash
# Kiểm tra số lượng docs trong Redis
docker exec plagiarism-backend python -c "
import redis
from app.config import settings
r = redis.from_url(settings.REDIS_URL, decode_responses=False)
print(f'Corpus size: {len(r.keys(\"doc:sig:*\"))} documents')
"
```

---

## 4. Chạy Test

### 4.1. Test API với cURL
```bash
# Test file có sẵn
curl -X POST "http://localhost:8000/api/v1/plagiarism/check" \
  -F "file=@docs_test/test_80_percent.txt"

# Xem kết quả đẹp hơn
curl -s -X POST "http://localhost:8000/api/v1/plagiarism/check" \
  -F "file=@docs_test/test_80_percent.txt" | python3 -m json.tool
```

### 4.2. Test Các Mức Độ Tương Đồng
Folder `docs_test/` chứa các file mẫu với các mức độ tương đồng khác nhau:

| File | Similarity thực tế | Level | Mô tả |
|------|-------------------|-------|-------|
| `test1.txt` | ~0% | none | Ít nội dung trùng khớp |
| `test2.txt` | ~0% | none | Trùng khớp rất thấp |
| `test3.txt` | ~28% | low | Trùng khớp thấp |
| `test4.txt` | ~50% | medium | Trùng khớp trung bình |
| `test5.txt` | ~47% | medium | Trùng khớp cao |

> **Lưu ý:** Mức độ similarity phụ thuộc vào corpus đã seed. Thuật toán MinHash/LSH so sánh n-gram shingles, không phải exact text matching.

### 4.3. Test Qua UI
1. Mở trình duyệt: http://localhost:3000
2. Đăng ký/Đăng nhập
3. Chọn tab "Kiểm tra"
4. Upload file từ `docs_test/`
5. Xem kết quả với matched segments

---

## 5. Truy Cập Ứng Dụng

| Service | URL | Mô tả |
|---------|-----|-------|
| Frontend | http://localhost:3000 | Giao diện người dùng |
| API Docs | http://localhost:8000/docs | Swagger UI |
| MinIO Console | http://localhost:9001 | File storage (minioadmin/minioadmin) |
| PostgreSQL | localhost:5432 | Database (postgres/postgres) |
| Redis | localhost:6379 | LSH Index |

---

## 6. Xử Lý Lỗi

### Lỗi: Container không start
```bash
# Xem logs
docker logs plagiarism-backend
docker logs plagiarism-frontend

# Restart tất cả
docker-compose down
docker-compose up -d
```

### Lỗi: corpus_size = 0
```bash
# Kiểm tra corpus trong PostgreSQL
docker exec -it plagiarism-backend python -c "
from app.db.database import SessionLocal
from app.db.models import Document
db = SessionLocal()
count = db.query(Document).filter(Document.is_corpus == 1).count()
print(f'Corpus trong PostgreSQL: {count} documents')
db.close()
"

# Nếu có data nhưng chưa sync Redis, chạy sync
docker exec -it plagiarism-backend python scripts/seed_corpus_matched.py --sync-only

# Restart backend
docker restart plagiarism-backend
```

### Lỗi: Redis connection failed
```bash
# Kiểm tra Redis
docker logs plagiarism-redis

# Restart Redis
docker restart plagiarism-redis plagiarism-backend
```

### Reset Toàn Bộ (Xóa Sạch Data)
```bash
# Dừng và xóa volumes
docker-compose down -v

# Khởi động lại từ đầu
./docker-start.sh --init-corpus
```

---

## 7. Commands Hữu Ích

```bash
# Xem trạng thái containers
docker-compose ps

# Xem logs real-time
docker-compose logs -f backend

# Vào shell container
docker exec -it plagiarism-backend bash

# Rebuild images (sau khi sửa code)
docker-compose build --no-cache
docker-compose up -d
```

---


