# PlagiarismGuard 2.0 - Quick Start Guide

## 🚀 Cách sử dụng

### Chỉ cần 1 bước: Click để chạy!
**Double-click vào file `start.sh`** hoặc:
```bash
./start.sh
```

Script sẽ tự động:
- ✅ Start Redis (nếu chưa chạy)
- ✅ Start Backend (port 8000)
- ✅ Start Frontend (port 3000)
- ✅ Mở browser tự động
- ✅ Hiển thị corpus stats

### Dừng server
Nhấn **Ctrl+C** trong terminal

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
curl http://localhost:8000/api/v1/plagiarism/corpus/stats
```

---

## 🐛 Troubleshooting

### Redis không start được
```bash
# Install Redis (nếu chưa có)
brew install redis

# Start Redis manually
redis-server --daemonize yes
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
