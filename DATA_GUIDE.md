# 📚 Hướng Dẫn Quản Lý Corpus Data - PlagiarismGuard

## 📊 Nguồn Dữ Liệu Hiện Tại

### 1. **Synthetic Data (Template-Based)**
Corpus hiện tại (6,000 documents) được tạo bằng **synthetic generation**:

**Script:** `backend/scripts/seed_corpus_matched.py`

**Phương pháp:**
- ✅ Đọc nội dung từ folder `docs_test/` (17 test files)
- ✅ Trích xuất 22-35% nội dung gốc từ test files
- ✅ Thêm nội dung mở rộng từ templates để đạt ~1000 từ/doc
- ✅ Tạo metadata ngẫu nhiên (tác giả, trường ĐH, năm)

**Template nguồn:**
```python
# Các template được định nghĩa trong script:
- INTRO_TEMPLATES: Phần mở đầu
- METHODOLOGY_TEMPLATES: Phương pháp nghiên cứu  
- TECHNICAL_PARAGRAPHS: Đoạn văn kỹ thuật
- CONCLUSION_TEMPLATES: Kết luận
- FILLER_PARAGRAPHS: Đoạn văn bổ sung
```

**Topics:** 30+ chủ đề công nghệ (AI, Học máy, Blockchain, DevOps, etc.)

**Universities:** 12 trường đại học Việt Nam

---

### 2. **Nguồn Dữ Liệu Khác (Chưa Sử Dụng)**

#### Wikipedia Tiếng Việt
Script `generate_corpus.py` có template để crawl Wikipedia nhưng **chưa triển khai đầy đủ**.

#### Web Crawling
`backend/scripts/crawlers/` chứa base crawler nhưng **chưa hoạt động**.

---

## 🚀 Cách Nạp Thêm Data

### **Phương Án 1: Sử dụng Script Có Sẵn (Khuyến Nghị)**

#### 1.1. Thêm Documents Từ Test Files

```bash
# Seed thêm 1000 docs matched với docs_test/
docker exec plagiarism-backend python scripts/seed_corpus_matched.py \
  --num-docs 1000 \
  --sync-redis
```

**Tùy chọn:**
- `--num-docs N`: Số lượng documents cần tạo
- `--sync-redis`: Đồng bộ luôn vào Redis LSH index
- Không có `--sync-redis`: Chỉ lưu PostgreSQL

#### 1.2. Restart Backend (Nếu Không Dùng --sync-redis)

```bash
docker restart plagiarism-backend
```

---

### **Phương Án 2: Import Từ File Text Có Sẵn**

#### 2.1. Chuẩn Bị Dữ Liệu

Tạo folder chứa file `.txt`:
```
/my-corpus-data/
  ├── doc1.txt
  ├── doc2.txt
  └── doc3.txt
```

#### 2.2. Sửa Script Import

Tạo file `backend/scripts/import_custom_corpus.py`:

```python
#!/usr/bin/env python3
"""
Import Custom Corpus from Text Files
"""
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import Document
from app.services.preprocessing.vietnamese_nlp import preprocess_vietnamese

def import_corpus(folder_path: str):
    db = SessionLocal()
    count = 0
    
    for txt_file in Path(folder_path).glob('*.txt'):
        with open(txt_file, 'r', encoding='utf-8') as f:
            text = f.read().strip()
        
        # Tokenize để đếm từ
        tokens = preprocess_vietnamese(text)
        word_count = len(tokens)
        
        # Tạo document
        doc = Document(
            id=uuid.uuid4(),
            title=txt_file.stem,  # Tên file làm title
            extracted_text=text,
            word_count=word_count,
            status='indexed',
            author='Unknown',
            university='Unknown',
            year=2024
        )
        
        db.add(doc)
        count += 1
        
        if count % 100 == 0:
            db.commit()
            print(f"Imported {count} documents...")
    
    db.commit()
    print(f"✅ Total imported: {count} documents")
    db.close()

if __name__ == '__main__':
    import sys
    folder = sys.argv[1] if len(sys.argv) > 1 else '/data/corpus'
    import_corpus(folder)
```

#### 2.3. Copy Data Vào Container

```bash
# Copy folder vào container
docker cp /path/to/my-corpus-data plagiarism-backend:/data/corpus

# Run import
docker exec plagiarism-backend python scripts/import_custom_corpus.py /data/corpus

# Restart để load vào Redis
docker restart plagiarism-backend
```

---

### **Phương Án 3: Import Từ CSV/Excel**

#### 3.1. Chuẩn Bị CSV

Format: `corpus.csv`
```csv
title,author,university,year,text
"Nghiên cứu AI","Nguyễn Văn A","ĐHBK HN",2023,"Nội dung..."
"Deep Learning","Trần Thị B","ĐHQG HCM",2024,"Nội dung..."
```

#### 3.2. Script Import CSV

```python
#!/usr/bin/env python3
import pandas as pd
import uuid
from app.db.database import SessionLocal
from app.db.models import Document
from app.services.preprocessing.vietnamese_nlp import preprocess_vietnamese

def import_from_csv(csv_path: str):
    db = SessionLocal()
    df = pd.read_csv(csv_path)
    
    for _, row in df.iterrows():
        tokens = preprocess_vietnamese(row['text'])
        
        doc = Document(
            id=uuid.uuid4(),
            title=row['title'],
            author=row['author'],
            university=row['university'],
            year=int(row['year']),
            extracted_text=row['text'],
            word_count=len(tokens),
            status='indexed'
        )
        db.add(doc)
    
    db.commit()
    print(f"✅ Imported {len(df)} documents")
    db.close()

if __name__ == '__main__':
    import sys
    csv_file = sys.argv[1]
    import_from_csv(csv_file)
```

#### 3.3. Chạy Import

```bash
# Install pandas nếu chưa có
docker exec plagiarism-backend pip install pandas

# Copy CSV vào container
docker cp corpus.csv plagiarism-backend:/app/corpus.csv

# Import
docker exec plagiarism-backend python scripts/import_from_csv.py /app/corpus.csv

# Restart
docker restart plagiarism-backend
```

---

### **Phương Án 4: Web Crawling (Nâng Cao)**

#### 4.1. Crawl Wikipedia Tiếng Việt

Sửa file `backend/scripts/crawlers/wikipedia_crawler.py` (nếu có) hoặc tạo mới.

#### 4.2. Crawl Academic Papers

Crawl từ các nguồn:
- Google Scholar
- ResearchGate
- VNU-EPrints
- Digital libraries của các trường ĐH

**Lưu ý:** Cần tuân thủ robots.txt và rate limiting.

---

## 🔄 Quy Trình Đầy Đủ Khi Nạp Data Mới

```bash
# 1. Nạp data vào PostgreSQL
docker exec plagiarism-backend python scripts/import_custom_corpus.py /data/corpus

# 2. Verify số lượng
docker exec plagiarism-backend python scripts/verify_corpus.py

# 3. Sync vào Redis LSH index (restart backend)
docker restart plagiarism-backend

# 4. Kiểm tra LSH index
docker exec plagiarism-backend python -c "
import redis
from app.config import settings
r = redis.from_url(settings.REDIS_URL, decode_responses=True)
print(f'Corpus size: {len(r.keys(\"doc:sig:*\"))}')
"

# 5. Test plagiarism check
curl -X POST "http://localhost:8000/api/v1/plagiarism/check" \
  -F "file=@test.txt"
```

---

## 📈 Thống Kê Corpus

```bash
# Xem tổng quan
./scripts/view_corpus.sh

# Verify yêu cầu (≥3000 docs, 500-1000 words)
docker exec plagiarism-backend python scripts/verify_corpus.py

# Query trực tiếp PostgreSQL
docker exec plagiarism-postgres psql -U postgres -d plagiarism
```

---

## ⚠️ Lưu Ý Quan Trọng

### 1. **Dung Lượng Redis**
- Mỗi document ~2-3KB trong Redis (signature + metadata)
- 10,000 docs ≈ 30MB RAM
- Adjust `maxmemory` trong `docker-compose.yml` nếu cần

### 2. **Performance PostgreSQL**
- Index được tạo tự động cho `status`, `word_count`
- Với >10,000 docs, cân nhắc partition tables

### 3. **Chất Lượng Data**
- Corpus cần đa dạng về topic và writing style
- Độ dài tài liệu nên tương đương với documents cần check
- MinHash/LSH hoạt động tốt nhất với documents có length tương tự

### 4. **Backup**
```bash
# Backup PostgreSQL
docker exec plagiarism-postgres pg_dump -U postgres plagiarism > backup.sql

# Restore
docker exec -i plagiarism-postgres psql -U postgres -d plagiarism < backup.sql
```

---

## 🎯 Roadmap Cải Tiến

### Ngắn Hạn
- [ ] Tích hợp Wikipedia API crawler
- [ ] Hỗ trợ import từ PDF/DOCX bulk
- [ ] Web interface để upload corpus

### Dài Hạn
- [ ] Crawl academic databases
- [ ] Auto-classification by topic
- [ ] Deduplication pipeline
- [ ] Quality scoring for corpus

---

## 📞 Troubleshooting

**Corpus size = 0 sau khi import:**
```bash
# Check PostgreSQL
docker exec plagiarism-postgres psql -U postgres -d plagiarism -c \
  "SELECT COUNT(*) FROM documents WHERE status='indexed';"

# Restart backend để load vào Redis
docker restart plagiarism-backend
```

**Redis hết memory:**
```yaml
# docker-compose.yml
redis:
  command: redis-server --maxmemory 8gb --maxmemory-policy allkeys-lru
```

**Import chậm:**
```python
# Batch commit trong script
if count % 1000 == 0:
    db.commit()
```

---

*Last updated: February 3, 2026*
