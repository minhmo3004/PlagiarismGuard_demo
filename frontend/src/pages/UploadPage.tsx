import React, { useState } from 'react';
import { Layout, Typography, Card, Space } from 'antd';
import { useNavigate } from 'react-router-dom';
import { FileUploader } from '../components/upload/FileUploader';
import { UploadButton } from '../components/upload/UploadButton';

const { Content } = Layout;
const { Title, Paragraph } = Typography;

/**
 * Trang Upload (Upload Page)
 * - Cho phép người dùng chọn file và bắt đầu kiểm tra đạo văn
 * - Sử dụng FileUploader để chọn file (kéo thả hoặc click)
 * - Hiển thị thông tin file đã chọn + nút "Kiểm tra đạo văn" khi có file
 * - Sau khi upload thành công → chuyển hướng đến trang kết quả (/result/:jobId)
 */
export const UploadPage: React.FC = () => {
  // File người dùng đã chọn (null nếu chưa chọn)
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const navigate = useNavigate();

  /**
   * Callback khi FileUploader chọn file thành công
   * - Lưu file vào state để hiển thị thông tin và kích hoạt nút upload
   */
  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
  };

  /**
   * Callback khi UploadButton upload thành công
   * - Nhận jobId từ server
   * - Chuyển hướng đến trang kết quả với jobId
   */
  const handleUploadSuccess = (jobId: string) => {
    navigate(`/result/${jobId}`);
  };

  return (
    <Layout>
      <Content style={{ padding: '50px', maxWidth: 800, margin: '0 auto' }}>
        {/* Header: tiêu đề trang + mô tả ngắn */}
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <Title level={2}>Kiểm tra đạo văn</Title>
          <Paragraph style={{ fontSize: 16, color: '#8c8c8c' }}>
            Upload tài liệu của bạn để bắt đầu kiểm tra
          </Paragraph>
        </div>

        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* Component chọn file (kéo thả hoặc click) */}
          <FileUploader onFileSelect={handleFileSelect} />

          {/* Hiển thị thông tin file + nút kiểm tra khi đã chọn file */}
          {selectedFile && (
            <Card>
              <div style={{ marginBottom: 16 }}>
                <strong>File đã chọn:</strong> {selectedFile.name}
              </div>
              <div style={{ marginBottom: 16 }}>
                <strong>Kích thước:</strong> {(selectedFile.size / 1024).toFixed(2)} KB
              </div>
              <div style={{ textAlign: 'center' }}>
                <UploadButton
                  file={selectedFile}
                  onSuccess={handleUploadSuccess}
                />
              </div>
            </Card>
          )}
        </Space>

        {/* Phần lưu ý (hướng dẫn người dùng) */}
        <Card style={{ marginTop: 40, background: '#f5f5f5' }}>
          <Title level={5}>Lưu ý:</Title>
          <ul style={{ marginBottom: 0 }}>
            <li>Định dạng hỗ trợ: PDF, DOCX, TXT, TEX</li>
            <li>Kích thước tối đa: 20MB</li>
            <li>Thời gian xử lý: 30 giây - 2 phút tùy độ dài tài liệu</li>
            <li>Kết quả sẽ được lưu trong lịch sử kiểm tra</li>
          </ul>
        </Card>
      </Content>
    </Layout>
  );
};