#!/bin/bash

# PlagiarismGuard 2.0 - Script khởi động
# Tự động khởi động Backend + Frontend

echo "🚀 Đang khởi động PlagiarismGuard 2.0..."
echo "=================================="

# Lấy thư mục chứa script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Tạo thư mục logs nếu chưa có
mkdir -p logs

# Hàm dọn dẹp khi thoát
cleanup() {
    echo ""
    echo "🛑 Đang dừng tất cả các dịch vụ..."
    pkill -f "uvicorn app.main:app"
    pkill -f "react-scripts start"
    echo "✅ Đã dừng tất cả dịch vụ"
    exit 0
}

# Bắt tín hiệu Ctrl+C
trap cleanup INT TERM

# Kiểm tra Redis có đang chạy không
echo ""
echo "📊 Đang kiểm tra Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis chưa chạy. Đang khởi động Redis..."
    
    # Thử khởi động Redis
    if command -v redis-server > /dev/null 2>&1; then
        # Khởi động Redis ở chế độ background
        redis-server --daemonize yes --port 6379 > /dev/null 2>&1
        sleep 2
        
        if redis-cli ping > /dev/null 2>&1; then
            echo "✅ Redis đã khởi động thành công"
        else
            echo "❌ Không thể khởi động Redis!"
            echo "   Vui lòng cài đặt Redis bằng lệnh:"
            echo "   brew install redis"
            exit 1
        fi
    else
        echo "❌ Redis chưa được cài đặt!"
        echo "   Vui lòng cài đặt Redis bằng lệnh:"
        echo "   brew install redis"
        exit 1
    fi
else
    echo "✅ Redis đang chạy"
fi

# Khởi động Backend
echo ""
echo "🔧 Đang khởi động Backend..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..
echo "✅ Backend đã khởi động (PID: $BACKEND_PID)"
echo "   URL: http://localhost:8000"
echo "   Logs: logs/backend.log"

# Chờ backend sẵn sàng
echo ""
echo "⏳ Đang chờ backend sẵn sàng..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend đã sẵn sàng!"
        break
    fi
    sleep 1
    echo -n "."
done

# Khởi động Frontend
echo ""
echo "⚛️  Đang khởi động Frontend..."
cd frontend
BROWSER=none npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "✅ Frontend đã khởi động (PID: $FRONTEND_PID)"
echo "   URL: http://localhost:3000"
echo "   Logs: logs/frontend.log"

# Chờ frontend sẵn sàng
echo ""
echo "⏳ Đang chờ frontend sẵn sàng..."
for i in {1..60}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend đã sẵn sàng!"
        break
    fi
    sleep 1
    echo -n "."
done

# Mở trình duyệt
echo ""
echo "🌐 Đang mở trình duyệt..."
sleep 2
open http://localhost:3000

# Hiển thị thông tin trạng thái
echo ""
echo "=================================="
echo "✅ PlagiarismGuard 2.0 đã chạy thành công!"
echo "=================================="
echo ""
echo "📍 Các địa chỉ truy cập:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📊 Thống kê Corpus:"
curl -s http://localhost:8000/api/v1/plagiarism/corpus/stats | python3 -m json.tool 2>/dev/null || echo "   (API chưa sẵn sàng)"
echo ""
echo "📝 Nhật ký log:"
echo "   Backend:  tail -f logs/backend.log"
echo "   Frontend: tail -f logs/frontend.log"
echo ""
echo "🛑 Nhấn Ctrl+C để dừng tất cả dịch vụ"
echo ""

# Giữ script chạy liên tục
wait