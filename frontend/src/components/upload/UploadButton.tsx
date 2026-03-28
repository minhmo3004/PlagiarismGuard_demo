import React, { useState } from 'react';
import { Button, message } from 'antd';
import { CheckCircleOutlined, LoadingOutlined } from '@ant-design/icons';
import { uploadDocumentPro } from '../../services/api';

// Định nghĩa props cho component UploadButton
interface UploadButtonProps {
  // File đã được chọn từ FileUploader (có thể null nếu chưa chọn)
  file: File | null;

  // Callback khi upload thành công, nhận job_id từ server
  onSuccess: (jobId: string) => void;

  // Trạng thái vô hiệu hóa nút (disabled)
  disabled?: boolean;
}

/**
 * Component nút "Kiểm Tra Đạo Văn" (Bản PRO - Asynchronous)
 * - Gọi API uploadDocumentPro để gửi file lên server
 * - Trả về job_id để frontend tiến hành polling
 */
export const UploadButton: React.FC<UploadButtonProps> = ({
  file,
  onSuccess,
  disabled = false,
}) => {
  // Trạng thái đang upload
  const [isUploading, setIsUploading] = useState(false);

  /**
   * Xử lý khi người dùng nhấn nút "Kiểm Tra Đạo Văn"
   */
  const handleClick = async () => {
    if (!file) {
      message.warning('Vui lòng chọn file trước');
      return;
    }

    setIsUploading(true);

    try {
      // Sử dụng API Pro để lấy job_id
      const response = await uploadDocumentPro(file);

      message.success('Đã gửi yêu cầu kiểm tra! Vui lòng chờ trong giây lát.');
      
      // Truyền job_id về để parent thực hiện navigate hoặc polling
      onSuccess(response.job_id);
    } catch (error: any) {
      console.error('Upload error:', error);
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'Lỗi khi gửi yêu cầu kiểm tra';

      message.error(errorMessage);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Button
      type="primary"
      size="large"
      icon={isUploading ? <LoadingOutlined /> : <CheckCircleOutlined />}
      disabled={disabled || isUploading || !file}
      loading={isUploading}
      onClick={handleClick}
    >
      {isUploading ? 'Đang gửi...' : 'Kiểm Tra Đạo Văn (Pro)'}
    </Button>
  );
};