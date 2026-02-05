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

### Bước 3: Khởi Động Docker (Không Seed)
```bash
# Chỉ khởi động services, không seed corpus
./docker-start.sh
```

### Bước 4: Khởi Động Docker + Seed 3000 Tài Liệu
```bash
# Khởi động + tự động seed 3000 tài liệu tiếng Việt
./docker-start.sh --init-corpus
```

> ⏱️ Thời gian seed: khoảng 2-3 phút cho 3000 tài liệu

---

## 3. Seed Corpus

### 3.1. Seed Tự Động (Khuyến Nghị)
```bash
./docker-start.sh --init-corpus
```

### 3.2. Seed Thủ Công
```bash
# Khởi động Docker trước
docker-compose up -d

# Chờ services healthy (~30s)
docker ps

# Seed 3000 tài liệu
docker exec plagiarism-backend python scripts/generate_corpus.py --num-docs 3000

# Restart backend để load corpus vào memory
docker restart plagiarism-backend
```

### 3.3. Tùy Chọn Số Lượng
| Lệnh | Số docs | Thời gian |
|------|---------|-----------|
| `--num-docs 100` | 100 | ~20 giây |
| `--num-docs 500` | 500 | ~1 phút |
| `--num-docs 1000` | 1000 | ~1.5 phút |
| `--num-docs 3000` | 3000 | ~3 phút |

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
# Seed lại
docker exec plagiarism-backend python scripts/generate_corpus.py --num-docs 3000

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

*Hướng dẫn tạo bởi PlagiarismGuard Team*
