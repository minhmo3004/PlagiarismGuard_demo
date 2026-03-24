# PlagiarismGuard 2.0

Hệ thống phát hiện đạo văn công nghiệp sử dụng MinHash + LSH để phát hiện bản sao gần giống.

## 📸 Xem trước

<p align="center">
  <img src="docs/images/upload-page.png" alt="Upload Page" width="100%"/>
  <br><em>Trang Tải lên - Tải lên tài liệu cần kiểm tra</em>
</p>

<p align="center">
  <img src="docs/images/result-page.png" alt="Result Page" width="100%"/>
  <br><em>Trang Kết quả - Hiển thị độ tương đồng và nguồn trùng khớp</em>
</p>

<p align="center">
  <img src="docs/images/history-page.png" alt="History Page" width="100%"/>
  <br><em>Trang Lịch sử - Quản lý các lần kiểm tra</em>
</p>

## 🎯 Tính năng

- **Thuật toán MinHash + LSH**: Phát hiện độ tương đồng nhanh chóng mà không cần đào tạo máy học
- **Xử lý ngôn ngữ tự nhiên tiếng Việt**: Tối ưu hóa cho văn bản tiếng Việt với `underthesea`
- **Khả năng mở rộng**: Xử lý hơn 1 triệu tài liệu với chỉ mục LSH Redis
- **Độ chính xác cao**: Độ chính xác ≥ 90%, Độ thu hồi ≥ 85%
- **Tốc độ nhanh**: Độ trễ truy vấn < 500ms

## 🏗️ Kiến trúc

```
Backend:  FastAPI + Celery + Redis + PostgreSQL + S3
Frontend: React 18 + TypeScript + Ant Design
Thuật toán: datasketch (MinHash/LSH) + underthesea (Xử lý ngôn ngữ tự nhiên tiếng Việt)
```

## 📚 Tài liệu

Xem `/docs/plan/` để biết tài liệu chi tiết:
- **[PROMPT.md](./docs/plan/PROMPT.md)** - Prompt để bắt đầu triển khai
- **[IMPLEMENTATION_STEPS.md](./docs/plan/IMPLEMENTATION_STEPS.md)** - Hướng dẫn từng bước
- **[README.md](./docs/plan/README.md)** - Mục lục tài liệu

## 🚀 Bắt đầu nhanh

### Điều kiện tiên quyết

- Python 3.9+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Thiết lập một lệnh

```bash
# Sao chép kho lưu trữ
git clone <repo-url>
cd Phat-Hien-Dao-Van-MinHash-LSH

# Chạy script thiết lập (cài đặt tất cả phụ thuộc)
chmod +x scripts/*.sh
./scripts/setup.sh
```

### Bắt đầu phát triển

```bash
# Khởi động cả backend và frontend
./scripts/run-dev.sh

# Truy cập:
# - Frontend:  http://localhost:3000
# - Backend:   http://localhost:8000
# - Tài liệu API:  http://localhost:8000/docs
```

### Thiết lập thủ công (Thay thế)

<details>
<summary>Nhấp để mở rộng hướng dẫn thiết lập thủ công</summary>

#### 1. Khởi động dịch vụ

```bash
# Khởi động Redis, PostgreSQL, MinIO
docker-compose up -d

# Chờ dịch vụ khỏe mạnh
docker-compose ps
```

#### 2. Thiết lập Backend

```bash
cd backend

# Tạo môi trường ảo
python -m venv venv
venv\Scripts\activate  # Trên IOS: source venv/bin/activate

# Cài đặt phụ thuộc
pip install -r requirements.txt

# Sao chép file môi trường
cp ../.env.example .env

# Chạy backend
uvicorn app.main:app --reload --port 8000
```

Backend sẽ có sẵn tại http://localhost:8000

#### 3. Thiết lập Frontend

```bash
cd frontend
npm install
npm start
```

Frontend sẽ có sẵn tại http://localhost:3000

</details>

## 📊 Tiến độ hiện tại

- [x] **Giai đoạn 1: Thiết lập dự án** (14 file) - HOÀN THÀNH
  - [x] Cấu trúc thư mục
  - [x] Dịch vụ Docker Compose
  - [x] Lược đồ cơ sở dữ liệu
  - [x] File cấu hình
  - [x] Mô hình Pydantic
  
- [x] **Giai đoạn 2: Thuật toán cốt lõi** (14 file) - HOÀN THÀNH
  - [x] Bộ tạo MinHash
  - [x] Bộ chỉ mục LSH
  - [x] Tiền xử lý văn bản
  - [x] Bộ tính độ tương đồng
  
- [x] **Giai đoạn 3: Lớp API** (10 file) - HOÀN THÀNH
  - [x] Điểm cuối FastAPI
  - [x] Tác vụ Celery
  - [x] Hỗ trợ WebSocket
  - [x] Xác thực
  
- [x] **Giai đoạn 4: Frontend** (19 file) - HOÀN THÀNH
  - [x] Thành phần React
  - [x] Hook tùy chỉnh
  - [x] Trang và định tuyến
  - [x] Tích hợp API
  
- [x] **Giai đoạn 5: Kiểm tra** (4 file) - HOÀN THÀNH
  - [x] Kiểm tra đơn vị
  - [x] Kiểm tra thành phần
  
- [x] **Giai đoạn 6: Script phát triển** (3 file) - HOÀN THÀNH
  - [x] Script thiết lập
  - [x] Script chạy
  - [x] Script kiểm tra

**Tổng cộng: 64 file đã tạo**

## 📚 Quản lý Corpus

### Bộ thu thập Wikipedia

Tự động thu thập Wikipedia tiếng Việt để mở rộng corpus:

```bash
# Thu thập 100 bài viết ngẫu nhiên
docker exec plagiarism-backend python scripts/crawl_wiki_import.py --random 100

# Thu thập từ danh mục công nghệ (AI, CS, IT, v.v.)
docker exec plagiarism-backend python scripts/crawl_wiki_import.py --tech-categories 50

# Thu thập danh mục cụ thể
docker exec plagiarism-backend python scripts/crawl_wiki_import.py \
    --category "Khoa_học_máy_tính" --limit 50

# Thu thập và đồng bộ với Redis ngay lập tức
docker exec plagiarism-backend python scripts/crawl_wiki_import.py \
    --random 200 --sync-redis
```

**Tính năng:**
- ✅ Thu thập bài viết ngẫu nhiên
- ✅ Nhắm mục tiêu dựa trên danh mục (8 danh mục công nghệ)
- ✅ Lọc chất lượng (tối thiểu 50 từ)
- ✅ Làm sạch văn bản tiếng Việt
- ✅ Tự động nhập vào cơ sở dữ liệu
- ✅ Đồng bộ LSH Redis

### Xác minh Corpus

```bash
# Kiểm tra thống kê corpus
docker exec plagiarism-backend python scripts/verify_corpus.py

# Kiểm tra số lượng bài viết Wikipedia
docker exec plagiarism-backend python scripts/check_wiki_corpus.py
```

**Tài liệu:**
- [`backend/scripts/WIKIPEDIA_CRAWLER.md`](backend/scripts/WIKIPEDIA_CRAWLER.md) - Hướng dẫn bộ thu thập đầy đủ
- [`DATA_GUIDE.md`](DATA_GUIDE.md) - Quản lý corpus chung

## 🧪 Kiểm tra

```bash
# Chạy tất cả kiểm tra (backend + frontend)
./scripts/run-tests.sh

# Chạy chỉ kiểm tra backend
cd backend && pytest tests/ -v --cov=app

# Chạy chỉ kiểm tra frontend
cd frontend && npm test

# Xem báo cáo bao phủ
open test-results/backend-coverage/index.html
open test-results/frontend-coverage/lcov-report/index.html
```

## 🛠️ Script phát triển

| Script | Mô tả |
|--------|-------------|
| `scripts/setup.sh` | Cài đặt tất cả phụ thuộc (thiết lập một lần) |
| `scripts/run-dev.sh` | Khởi động backend + frontend đồng thời |
| `scripts/run-tests.sh` | Chạy tất cả kiểm tra với báo cáo bao phủ |

## 📁 Cấu trúc dự án

```
├── backend/              # Backend FastAPI
│   ├── app/
│   │   ├── api/         # Điểm cuối API
│   │   ├── core/        # Cấu hình cốt lõi
│   │   ├── db/          # Cơ sở dữ liệu
│   │   ├── models/      # Mô hình SQLAlchemy
│   │   ├── schemas/     # Lược đồ Pydantic
│   │   └── services/    # Logic nghiệp vụ
│   └── tests/           # Kiểm tra backend
├── frontend/            # Frontend React
│   ├── src/
│   │   ├── components/  # Thành phần React
│   │   ├── hooks/       # Hook tùy chỉnh
│   │   ├── pages/       # Thành phần trang
│   │   └── services/    # Dịch vụ API
│   └── __tests__/       # Kiểm tra frontend
├── scripts/             # Script phát triển
├── docs/                # Tài liệu
└── docker-compose.yml   # Dịch vụ Docker
```




