# PlagiarismGuard 2.0 - Kiến Trúc Hệ Thống Chi Tiết

## Mục Lục

1. [Quy Trình Tạo Database Trên Docker](#1-quy-trình-tạo-database-trên-docker)
2. [Luồng Dữ Liệu](#2-luồng-dữ-liệu)
3. [Vai Trò Từng Database](#3-vai-trò-từng-database)
4. [Schema Database](#4-schema-database)
5. [API Endpoints](#5-api-endpoints)
6. [Thuật Toán &amp; Lưu Trữ](#6-thuật-toán--lưu-trữ)

---

## 1. Quy Trình Tạo Database Trên Docker

### 1.1. Tổng Quan Docker Compose

```
┌─────────────────────────────────────────────────────────────┐
│                    DOCKER COMPOSE                           │
├─────────────────┬─────────────────┬─────────────────────────┤
│   INFRASTRUCTURE SERVICES         │   APPLICATION SERVICES  │
├────────────┬────────┬─────────────┼─────────────────────────┤
│ PostgreSQL │ Redis  │   MinIO     │  Backend  │  Frontend   │
│   :5432    │ :6379  │:9000/:9001  │   :8000   │   :3000     │
└────────────┴────────┴─────────────┴───────────┴─────────────┘
```

### 1.2. Thứ Tự Khởi Động

```
1. Redis         → Khởi động đầu tiên (healthcheck: redis-cli ping)
2. PostgreSQL    → Khởi động song song (healthcheck: pg_isready)
3. MinIO         → Khởi động song song (healthcheck: curl /minio/health/live)
4. Backend       → Chờ 3 services trên healthy → Khởi động
5. Frontend      → Chờ Backend → Khởi động
```

### 1.3. Docker Volumes (Lưu Trữ Persistent)

| Volume              | Mount Path                   | Mục đích                        |
| ------------------- | ---------------------------- | ---------------------------------- |
| `redis_data`      | `/data`                    | Lưu LSH index, corpus signatures  |
| `postgres_data`   | `/var/lib/postgresql/data` | Metadata users, documents, results |
| `minio_data`      | `/data`                    | Lưu file gốc (PDF, DOCX, TXT)    |
| `backend_uploads` | `/app/uploads`             | Thư mục tạm upload              |

### 1.4. Environment Variables Quan Trọng

```bash
# Backend → PostgreSQL
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/plagiarism

# Backend → Redis  
REDIS_URL=redis://redis:6379

# Backend → MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_UPLOADS=plagiarism-uploads
MINIO_BUCKET_CORPUS=plagiarism-corpus
```

> **Lưu ý**: Trong Docker network, các service gọi nhau bằng **hostname** (postgres, redis, minio), không phải localhost.

---

## 2. Luồng Dữ Liệu

### 2.1. Luồng Upload & Check Đạo Văn

```
┌──────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ FRONTEND │───▶│   BACKEND   │───▶│    MinIO    │───▶│ PostgreSQL  │
│  (React) │    │  (FastAPI)  │    │   (Files)   │    │ (Metadata)  │
└──────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      │                │                                      ▲
      │                │         ┌─────────────┐              │
      │                └────────▶│    Redis    │──────────────┘
      │                          │ (LSH Index) │
      │                          └─────────────┘
      │                                │
      └────────────────────────────────┘
                    (Result)
```

### 2.2. Chi Tiết Từng Bước

#### Bước 1: User Upload File (FE → BE)

```javascript
// Frontend: src/pages/UploadPage.tsx
POST /api/v1/plagiarism/check
Content-Type: multipart/form-data
Body: { file: <PDF/DOCX/TXT> }
```

#### Bước 2: Backend Xử Lý File

```python
# Backend: app/api/routes/plagiarism.py

1. Nhận file từ request
2. Lưu file tạm vào /app/uploads/
3. Extract text:
   - PDF → PyMuPDF (fitz)
   - DOCX → python-docx
   - TXT → đọc trực tiếp
4. Preprocess text:
   - Normalize (Unicode, lowercase)
   - Tokenize (Vietnamese NLP / underthesea)
```

#### Bước 3: MinIO Lưu File Gốc

```python
# Backend: app/services/minio_storage.py

1. Tính SHA256 hash của file (chống duplicate)
2. Upload file lên bucket "plagiarism-uploads"
3. Object path: uploads/{user_id}/{timestamp}_{filename}
```

#### Bước 4: Redis Query LSH Index

```python
# Backend: app/services/plagiarism_checker.py

1. Tạo MinHash signature từ extracted text
2. Query LSH index trong Redis
3. Lấy top 20 candidates có similarity > 0.2
4. So sánh chi tiết với từng candidate
5. Tìm matched segments (đoạn text giống nhau)
```

#### Bước 5: PostgreSQL Lưu Kết Quả

```python
# Backend: models.py

1. Tạo record trong bảng "check_results"
2. Lưu chi tiết matches trong bảng "match_details"
3. Trả về result_id cho frontend
```

#### Bước 6: Frontend Hiển Thị Kết Quả

```javascript
// Frontend: src/pages/ResultPage.tsx

1. Nhận JSON response từ API
2. Hiển thị overall_similarity (%)
3. Hiển thị danh sách matches
4. Expand để xem matched_segments
```

---

## 3. Vai Trò Từng Database

### 3.1. PostgreSQL - Metadata & Audit

```
┌──────────────────────────────────────────────────────────┐
│                      POSTGRESQL                          │
├──────────────────────────────────────────────────────────┤
│  Lưu thông tin có cấu trúc (relational data)             │
│  Users (tài khoản, tier, quota)                          │
│  Documents (metadata: title, author, university...)      │
│  Check Results (similarity score, processing time)       │
│  Match Details (matched segments, source info)           │
│  Audit trail (created_at, updated_at)                    │
└──────────────────────────────────────────────────────────┘
```

**Tại sao dùng PostgreSQL?**

- ACID transactions (đảm bảo data consistency)
- Complex queries (JOIN, aggregation)
- Quan hệ foreign key giữa users ↔ documents ↔ results
- Hỗ trợ UUID native

### 3.2. Redis - LSH Index & Cache

```
┌───────────────────────────────────────────────────┐
│                      REDIS                        │
├───────────────────────────────────────────────────┤
│  LSH Index (MinHash signatures)                   │
│  Corpus signatures (doc:sig:{doc_id})             │
│  Corpus metadata (doc:meta:{doc_id})              │
│  Corpus text (doc:text:{doc_id})                  │
│  Cache kết quả (tránh re-compute)                 │
│  Job queue (Celery broker - optional)             │
└───────────────────────────────────────────────────┘
```

**Key Patterns trong Redis:**

| Key Pattern           | Data Type     | Nội dung                              |
| --------------------- | ------------- | -------------------------------------- |
| `doc:sig:{doc_id}`  | String (JSON) | MinHash signature (128 integers)       |
| `doc:meta:{doc_id}` | Hash          | title, author, university, year        |

> **⚠️ LƯU Ý QUAN TRỌNG:** Full text **KHÔNG** được lưu trong Redis để tiết kiệm RAM.
> Text được lưu trong PostgreSQL (`documents.extracted_text`) và query khi cần tìm matched_segments.

**Tại sao dùng Redis?**

- In-memory → Query cực nhanh (< 1ms)
- Phù hợp cho LSH index (read-heavy)
- Chỉ lưu signatures + metadata (lightweight)
- Persist data với AOF (Append Only File)
- Hỗ trợ SET operations cho MinHash

### 3.3. MinIO - File Storage (S3-compatible)

```
┌──────────────────────────────────────────────────────────┐
│                         MINIO                            │
├──────────────────────────────────────────────────────────┤
│  Lưu file gốc (PDF, DOCX, TXT, TEX)                      │
│  Bucket: plagiarism-uploads (user uploads)               │
│  Bucket: plagiarism-corpus (corpus documents)            │
│  Hỗ trợ presigned URLs (download trực tiếp)              │
│  Content-addressable storage (SHA256 hash)               │
└──────────────────────────────────────────────────────────┘
```

**Bucket Structure:**

```
plagiarism-uploads/
├── user_123/
│   ├── 1706789012_thesis.pdf
│   └── 1706789056_report.docx
└── anonymous/
    └── 1706789100_test.txt

plagiarism-corpus/
├── corpus/
│   ├── doc_001.txt
│   └── doc_002.pdf
```

**Tại sao dùng MinIO?**

- S3-compatible API (dễ migrate lên AWS sau này)
- Không giới hạn kích thước file
- Hỗ trợ versioning
- Web console UI tại port 9001

---

## 4. Schema Database

### 4.1. ER Diagram

```
┌─────────────────┐       ┌──────────────────┐
│      users      │       │    documents     │
├─────────────────┤       ├──────────────────┤
│ id (UUID) PK    │───┐   │ id (UUID) PK     │
│ email           │   │   │ owner_id FK ─────│──┐
│ password_hash   │   │   │ title            │  │
│ tier            │   │   │ original_filename│  │
│ daily_uploads   │   │   │ s3_path          │  │
│ daily_checks    │   │   │ file_hash_sha256 │  │
│ last_reset_date │   │   │ file_size_bytes  │  │
│ created_at      │   │   │ word_count       │  │
│ updated_at      │   │   │ extracted_text   │  │
└─────────────────┘   │   │ status           │  │
                      │   │ created_at       │  │
                      │   └──────────────── ─┘  │
                      │                         │
                      │   ┌───────────────────┐ │
                      │   │  check_results    │ │
                      │   ├───────────────────┤ │
                      └──▶│ user_id FK        │ │
                          │ id (UUID) PK      │ │
                          │ query_doc_id FK   │◀┘
                          │ query_filename    │
                          │ overall_similarity│
                          │ plagiarism_level  │
                          │ match_count       │
                          │ processing_time_ms│
                          │ file_path         │
                          │ created_at        │
                          └────────┬──────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │  match_details   │
                          ├──────────────────┤
                          │ id (UUID) PK     │
                          │ result_id FK     │
                          │ source_doc_id FK │
                          │ similarity_score │
                          │ matched_segments │ ←── JSON array
                          │ source_title     │
                          │ source_author    │
                          │ source_university│
                          │ source_year      │
                          │ created_at       │
                          └──────────────────┘
```

### 4.2. Chi Tiết Từng Bảng

#### Bảng `users`

| Column          | Type         | Description                       |
| --------------- | ------------ | --------------------------------- |
| id              | UUID         | Primary key                       |
| email           | VARCHAR(255) | Email đăng nhập (unique)       |
| password_hash   | VARCHAR(255) | Bcrypt hashed password            |
| tier            | VARCHAR(20)  | 'free' / 'premium' / 'enterprise' |
| daily_uploads   | INTEGER      | Số file đã upload trong ngày  |
| daily_checks    | INTEGER      | Số lần check trong ngày        |
| last_reset_date | DATETIME     | Ngày reset quota gần nhất      |

#### Bảng `documents`

| Column            | Type         | Description                               |
| ----------------- | ------------ | ----------------------------------------- |
| id                | UUID         | Primary key                               |
| owner_id          | UUID FK      | User đã upload (nullable cho anonymous) |
| title             | VARCHAR(500) | Tiêu đề tài liệu                     |
| original_filename | VARCHAR(255) | Tên file gốc                            |
| s3_path           | VARCHAR(500) | Đường dẫn trên MinIO                 |
| file_hash_sha256  | VARCHAR(64)  | Hash chống duplicate                     |
| file_size_bytes   | BIGINT       | Kích thước file                        |
| word_count        | INTEGER      | Số từ                                   |
| extracted_text    | TEXT         | Nội dung đã extract                    |
| status            | VARCHAR(20)  | 'processing'/'indexed'/'failed'           |

#### Bảng `check_results`

| Column             | Type          | Description                    |
| ------------------ | ------------- | ------------------------------ |
| id                 | UUID          | Primary key                    |
| user_id            | UUID FK       | User thực hiện check         |
| query_filename     | VARCHAR(255)  | Tên file được check        |
| overall_similarity | NUMERIC(5,4)  | % tổng thể (0.0000 - 1.0000) |
| plagiarism_level   | VARCHAR(20)   | 'none'/'low'/'medium'/'high'   |
| match_count        | INTEGER       | Số nguồn trùng khớp        |
| processing_time_ms | INTEGER       | Thời gian xử lý (ms)        |
| file_path          | VARCHAR(1000) | MinIO object key               |

#### Bảng `match_details`

| Column            | Type         | Description                    |
| ----------------- | ------------ | ------------------------------ |
| id                | UUID         | Primary key                    |
| result_id         | UUID FK      | Thuộc check_result nào       |
| source_doc_id     | UUID FK      | Tài liệu nguồn trong corpus |
| similarity_score  | NUMERIC(5,4) | % giống với nguồn này      |
| matched_segments  | TEXT (JSON)  | Chi tiết từng đoạn giống  |
| source_title      | VARCHAR(500) | Tiêu đề nguồn              |
| source_author     | VARCHAR(255) | Tác giả nguồn               |
| source_university | VARCHAR(255) | Trường đại học            |
| source_year       | INTEGER      | Năm xuất bản                |

**Format của matched_segments (JSON):**

```json
[
  {
    "query_text": "Trí tuệ nhân tạo đang phát triển...",
    "query_start": 0,
    "query_end": 50,
    "source_text": "Trí tuệ nhân tạo đang phát triển...",
    "source_start": 120,
    "source_end": 170
  }
]
```

---

## 5. API Endpoints

### 5.1. Authentication (`/api/v1/auth`)

| Method | Endpoint      | Màn hình    | Mô tả                         |
| ------ | ------------- | ------------- | ------------------------------- |
| POST   | `/register` | Register Page | Đăng ký tài khoản mới     |
| POST   | `/login`    | Login Page    | Đăng nhập, trả JWT token    |
| POST   | `/refresh`  | (Auto)        | Refresh access token            |
| GET    | `/me`       | Profile       | Lấy thông tin user hiện tại |
| POST   | `/logout`   | Header        | Đăng xuất                    |

### 5.2. Plagiarism Check (`/api/v1/plagiarism`)

| Method | Endpoint                   | Màn hình   | Mô tả                            |
| ------ | -------------------------- | ------------ | ---------------------------------- |
| POST   | `/check`                 | Upload Page  | **Upload file & check ngay** |
| GET    | `/corpus/stats`          | Dashboard    | Thống kê corpus (số docs)       |
| GET    | `/history`               | History Page | Lịch sử check (paginated)        |
| DELETE | `/history/{id}`          | History Page | Xóa 1 record                      |
| GET    | `/history/{id}/download` | History Page | Tải file gốc                     |
| DELETE | `/history`               | History Page | Xóa toàn bộ lịch sử           |

### 5.3. Advanced Check (`/api/v1/check`) - Với Auth

| Method | Endpoint             | Màn hình   | Mô tả                       |
| ------ | -------------------- | ------------ | ----------------------------- |
| POST   | `/upload`          | Upload Page  | Upload & queue background job |
| GET    | `/{job_id}/status` | (Polling)    | Trạng thái job              |
| GET    | `/{job_id}/result` | Result Page  | Kết quả chi tiết           |
| POST   | `/{job_id}/cancel` | Upload Page  | Hủy job đang chờ           |
| POST   | `/{job_id}/retry`  | Result Page  | Thử lại job failed          |
| DELETE | `/{job_id}`        | History Page | Xóa job                      |
| GET    | `/history`         | History Page | Lịch sử user                |

### 5.4. Mapping API → Màn Hình

```
┌─────────────────┐     ┌─────────────────────────────────────┐
│   LOGIN PAGE    │────▶│ POST /auth/login                    │
│   REGISTER PAGE │────▶│ POST /auth/register                 │
└─────────────────┘     └─────────────────────────────────────┘

┌─────────────────┐     ┌─────────────────────────────────────┐
│   UPLOAD PAGE   │────▶│ POST /plagiarism/check              │
│   (Check ngay)  │     │ (upload file, trả kết quả ngay)     │
└─────────────────┘     └─────────────────────────────────────┘

┌─────────────────┐     ┌─────────────────────────────────────┐
│   RESULT PAGE   │────▶│ Response từ /plagiarism/check       │
│                 │     │ - overall_similarity                │
│                 │     │ - plagiarism_level                  │
│                 │     │ - matches[]                         │
│                 │     │   - matched_segments[]              │
└─────────────────┘     └─────────────────────────────────────┘

┌─────────────────┐     ┌─────────────────────────────────────┐
│   HISTORY PAGE  │────▶│ GET  /plagiarism/history            │
│                 │────▶│ DELETE /plagiarism/history/{id}     │
│                 │────▶│ GET  /plagiarism/history/{id}/download│
└─────────────────┘     └─────────────────────────────────────┘
```

---

## 6. Thuật Toán & Lưu Trữ

### 6.1. MinHash + LSH Algorithm

```
                    INPUT TEXT
                        │
                        ▼
              ┌─────────────────┐
              │   NORMALIZE     │  Unicode → lowercase → remove special chars
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   TOKENIZE      │  underthesea (Vietnamese NLP)
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   SHINGLING     │  k=7 (7-grams từ tokens)
              │   (k-grams)     │  MurmurHash3 → Set[int]
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │    MINHASH      │  128 hash functions
              │  (Signature)    │  Output: [int; 128]
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   LSH INDEX     │  threshold=0.4
              │   (Banding)     │  b=32 bands, r=4 rows
              └─────────────────┘
```

### 6.2. Tham Số Config

```python
# backend/app/config.py

# MinHash
MINHASH_PERMUTATIONS = 128    # Số hash functions (độ chính xác ≈ 1/√128 ≈ 8.8%)
MINHASH_SEED = 42             # Seed cố định để reproducible

# Shingling
SHINGLE_SIZE = 7              # k-gram size (tối ưu cho tiếng Việt)

# LSH
LSH_THRESHOLD = 0.4           # Ngưỡng similarity để coi là candidate
LSH_BANDS = 32                # Số bands (b)
LSH_ROWS = 4                  # Rows per band (r) → b*r = 128
```

### 6.3. Nơi Lưu Trữ Thuật Toán

#### Redis Keys cho Corpus (Lightweight - tiết kiệm RAM):

```
doc:sig:{doc_id}     ─── MinHash signature (JSON array [int; 128])
doc:meta:{doc_id}    ─── Metadata (Hash: title, author, year...)
```

> **Full text được lưu trong PostgreSQL** (`documents.extracted_text`), không phải Redis.
> Khi cần tìm matched_segments, hệ thống query từ PostgreSQL.

**Ví dụ thực tế:**

```redis
# Signature
GET doc:sig:abc123
→ "[1234567890, 9876543210, ..., 128 integers]"

# Metadata
HGETALL doc:meta:abc123
→ {
    "title": "Nghiên cứu về AI trong Y tế",
    "author": "Nguyễn Văn An",
    "university": "ĐHQG TP.HCM",
    "year": "2023",
    "word_count": "542"
  }
```

**PostgreSQL (lưu text lâu dài):**
```sql
SELECT extracted_text FROM documents WHERE id = 'abc123...' AND is_corpus = 1;
→ "Trí tuệ nhân tạo đang được ứng dụng rộng rãi trong lĩnh vực y tế..."
```

### 6.4. Luồng Query LSH

```python
# backend/app/services/plagiarism_checker.py

def check_against_corpus(file_path, filename):
    # 1. Extract text từ file
    text = extract_text(file_path)
  
    # 2. Tạo MinHash signature
    tokens = preprocess_vietnamese(normalize_text(text))
    shingles = create_shingles(tokens, k=7)
    minhash = create_minhash_signature(shingles)
  
    # 3. Query LSH index (Redis) → Top 20 candidates
    candidates = lsh_index.query(minhash, top_k=20)
  
    # 4. Với mỗi candidate, tính similarity chính xác
    matches = []
    for doc_id, estimated_similarity in candidates:
        if estimated_similarity >= 0.2:
            # Lấy metadata từ Redis (fast, lightweight)
            metadata = redis.hgetall(f"doc:meta:{doc_id}")
            
            # Lấy source text từ PostgreSQL (không phải Redis - tiết kiệm RAM)
            source_text = db.query(Document).filter(Document.id == doc_id).first().extracted_text
          
            # Tìm matched segments
            segments = find_common_shingles(tokens, source_tokens)
          
            matches.append({
                "doc_id": doc_id,
                "similarity": estimated_similarity,
                "matched_segments": segments
            })
  
    return PlagiarismResult(
        overall_similarity=max_similarity,
        matches=matches
    )
```

### 6.5. LSH Banding Technique

```
MinHash Signature: [h1, h2, h3, ..., h128]

Chia thành 32 bands, mỗi band 4 rows:
Band 1: [h1, h2, h3, h4]
Band 2: [h5, h6, h7, h8]
...
Band 32: [h125, h126, h127, h128]

Hai documents là CANDIDATES nếu match ít nhất 1 band.

Probability công thức:
P(candidate | similarity = s) = 1 - (1 - s^r)^b
                               = 1 - (1 - s^4)^32

Ví dụ:
- s = 0.4 (40% similar) → P ≈ 0.76 (76% chance được detect)
- s = 0.5 (50% similar) → P ≈ 0.97 (97% chance)
- s = 0.6 (60% similar) → P ≈ 0.9997 (gần như chắc chắn)
```

---

## 7. Tổng Kết

### Storage Summary

| Loại Data             | Lưu ở đâu   | Tại sao                          |
| ---------------------- | ------------- | --------------------------------- |
| User info, metadata    | PostgreSQL    | ACID, relations                   |
| Check results          | PostgreSQL    | Audit, history                    |
| Match details          | PostgreSQL    | JSON trong TEXT column            |
| **Corpus text**        | **PostgreSQL**| **Tiết kiệm RAM (không dùng Redis)** |
| MinHash signatures     | Redis         | Fast query, in-memory             |
| Corpus metadata        | Redis         | Lightweight, quick display        |
| Original files         | MinIO         | Large files, S3-compatible        |

> **Best Practice:** Redis chỉ lưu signatures + metadata (lightweight). 
> Full text lưu trong PostgreSQL vì Redis chạy trên RAM, không phù hợp lưu trữ lâu dài.

### Data Flow Summary

```
User Upload → Backend → MinIO (save file)
                     → Redis (query LSH by signature)
                     → PostgreSQL (query text for segment matching)
                     → PostgreSQL (save result + match_details)
                     → Response → Frontend (display)
```

---

*Document version: 2.1*
*Last updated: 2026-02-03*
