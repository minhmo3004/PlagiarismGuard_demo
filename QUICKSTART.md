# PlagiarismGuard 2.0 - Quick Start Guide

## 🚀 Cách sử dụng

### Bước 1: Khởi động Docker
```bash
docker-compose up -d
```

### Bước 2: Setup Corpus (chỉ chạy 1 lần khi deploy máy mới)
```bash
./scripts/setup-corpus.sh
```
Script sẽ tự động crawl ~1000 tài liệu:
- 500 bài Wikipedia tiếng Việt random
- 300 bài Wikipedia tech categories (AI, ML, IT...)
- 200 papers ArXiv (AI, ML, CV, NLP, Security)

⏱️ **Thời gian:** ~15-20 phút

### Bước 3: Mở ứng dụng
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000

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

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## 📊 Check Corpus

```bash
./scripts/wiki-corpus.sh check
```

---

## 🐛 Troubleshooting

### Redis không start được
```bash
# Install Redis (nếu chưa có)
docker-compose up -d redis

# Start Redis manually
docker-compose up -d
```

### Port đã được sử dụng
```bash
# Kill backend
pkill -f "uvicorn app.main:app"

# Kill frontend
pkill -f "react-scripts start"
```

### Xem logs
```bash
# Backend
tail -f logs/backend.log

# Frontend
tail -f logs/frontend.log
```
