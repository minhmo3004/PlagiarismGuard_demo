# 📚 Hướng Dẫn Seed Corpus - PlagiarismGuard

## Yêu Cầu
- Docker & Docker Compose đã cài đặt
- Git (để clone repo)

---

## 🚀 Cách 1: Setup Nhanh (1 lệnh)

```bash
# Clone repo (nếu chưa có)
git clone <your-repo-url>
cd PlagiarismGuard_demo

# Tạo file .env từ template
cp .env.example .env

# Chạy setup tự động
./docker-start.sh
```

Script `docker-start.sh` sẽ tự động:
1. Khởi động Docker containers
2. Chờ services healthy
3. Seed 3000 tài liệu tiếng Việt
4. Restart backend để load corpus

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

### Bước 4: Seed corpus
```bash
# Seed 3000 tài liệu (mất ~2-3 phút)
docker exec plagiarism-backend python scripts/generate_corpus.py --num-docs 3000

# Hoặc seed ít hơn để test nhanh
docker exec plagiarism-backend python scripts/generate_corpus.py --num-docs 100
```

### Bước 5: Restart backend để load corpus vào LSH index
```bash
docker restart plagiarism-backend
```

### Bước 6: Kiểm tra
```bash
# Test API
curl -s -X POST "http://localhost:8000/api/v1/plagiarism/check" \
  -F "file=@docs_test/test_plagiarized.txt" | python3 -m json.tool

# corpus_size phải > 0
```

---

## 📊 Tùy Chọn Seed

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

### Lỗi: corpus_size = 0
```bash
# Chạy lại seed
docker exec plagiarism-backend python scripts/generate_corpus.py --num-docs 3000

# Restart backend
docker restart plagiarism-backend
```

### Lỗi: Container không start
```bash
# Xem logs để debug
docker logs plagiarism-backend
docker logs plagiarism-frontend
```

---

## 🔄 Reset Toàn Bộ

Nếu muốn xóa sạch và bắt đầu lại:
```bash
# Dừng và xóa containers + volumes
docker-compose down -v

# Khởi động lại
docker-compose up -d

# Seed lại corpus
docker exec plagiarism-backend python scripts/generate_corpus.py --num-docs 3000
docker restart plagiarism-backend
```

---

## ✅ Kiểm Tra Thành Công

Khi seed xong, bạn sẽ thấy output như sau:
```
==================================================
CORPUS GENERATION COMPLETE
Total generated: 3000
Total indexed: 3000
Failed: 0
Average word count: 542
==================================================
```

Và khi gọi API check, `corpus_size` phải là 3000+.

---

## 📚 Nguồn Dữ Liệu Corpus

**Corpus hiện tại (6,000 docs):**
- 🔹 **Nguồn:** Synthetic data từ templates
- 🔹 **Base:** Nội dung từ `docs_test/` (17 files)
- 🔹 **Mở rộng:** Templates văn bản học thuật tiếng Việt
- 🔹 **Topics:** 30+ chủ đề công nghệ (AI, Blockchain, DevOps...)
- 🔹 **Metadata:** 12 trường ĐH, 1,849 tác giả, 2018-2024

**Cách nạp thêm data:** Xem chi tiết tại [DATA_GUIDE.md](DATA_GUIDE.md)

