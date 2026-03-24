-- migrations/001_initial_schema.sql
-- PlagiarismGuard 2.0 - Script tạo cấu trúc cơ sở dữ liệu ban đầu

-- Bảng người dùng
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    tier VARCHAR(20) DEFAULT 'free' CHECK (tier IN ('free', 'premium', 'enterprise', 'admin')),
    daily_uploads INTEGER DEFAULT 0,
    daily_checks INTEGER DEFAULT 0,
    last_reset_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng tài liệu (bao gồm cả tài liệu người dùng upload và tài liệu corpus)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(500),
    original_filename VARCHAR(255),
    s3_path VARCHAR(500) NOT NULL,
    file_hash_sha256 VARCHAR(64) UNIQUE NOT NULL,
    file_size_bytes BIGINT,
    word_count INTEGER,
    page_count INTEGER,
    language VARCHAR(10) DEFAULT 'vi',
    extraction_method VARCHAR(50),
    status VARCHAR(20) DEFAULT 'processing' CHECK (status IN ('processing', 'indexed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    indexed_at TIMESTAMP
);

-- Bảng kết quả kiểm tra đạo văn
CREATE TABLE check_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    query_doc_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    query_filename VARCHAR(255),
    overall_similarity DECIMAL(5,4),
    match_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'done', 'failed', 'cancelled')),
    error_message TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Bảng chi tiết các đoạn khớp (match details)
CREATE TABLE match_details (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    result_id UUID REFERENCES check_results(id) ON DELETE CASCADE,
    source_doc_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    similarity_score DECIMAL(5,4),
    matched_segments JSONB,           -- Lưu mảng các đoạn văn bản trùng khớp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Các index hỗ trợ truy vấn nhanh
CREATE INDEX idx_documents_owner ON documents(owner_id);
CREATE INDEX idx_documents_hash ON documents(file_hash_sha256);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_created ON documents(created_at);

CREATE INDEX idx_results_user ON check_results(user_id);
CREATE INDEX idx_results_status ON check_results(status);
CREATE INDEX idx_results_created ON check_results(created_at);

CREATE INDEX idx_match_result ON match_details(result_id);

-- Function tự động cập nhật cột updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger cập nhật updated_at cho bảng users
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Thêm tài khoản admin mặc định (mật khẩu: admin123)
-- LƯU Ý: Hãy thay đổi mật khẩu này ngay trong môi trường production!
-- Password hash được tạo bằng bcrypt
INSERT INTO users (email, password_hash, tier) VALUES 
('admin@plagiarismguard.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEm8u6', 'admin');