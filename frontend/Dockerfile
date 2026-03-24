# Dockerfile cho Frontend - PlagiarismGuard

# Stage 1: Builder - Build ứng dụng React
FROM node:18-alpine AS builder

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy file package.json và package-lock.json (nếu có)
COPY package*.json ./

# Cài đặt dependencies 
# Sử dụng --legacy-peer-deps để tương thích với một số package cũ
RUN npm install --legacy-peer-deps

# Copy toàn bộ source code vào container
COPY . .

# Build ứng dụng React (tạo thư mục build/)
RUN npm run build

# Stage 2: Production - Sử dụng Nginx để phục vụ file tĩnh
FROM nginx:alpine

# Copy file cấu hình Nginx tùy chỉnh
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy thư mục build từ stage builder vào Nginx
COPY --from=builder /app/build /usr/share/nginx/html

# Mở port 80
EXPOSE 80

# Health check - Kiểm tra ứng dụng có đang chạy không
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

# Chạy Nginx ở chế độ foreground
CMD ["nginx", "-g", "daemon off;"]