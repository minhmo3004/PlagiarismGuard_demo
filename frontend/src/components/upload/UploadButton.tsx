import React, { useState } from 'react';
import { Button, message } from 'antd';
import { CheckCircleOutlined, LoadingOutlined } from '@ant-design/icons';
import { uploadDocument } from '../../services/api';

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
 * Component nút "Kiểm Tra Đạo Văn"
 * - Hiển thị trạng thái loading khi đang upload
 * - Gọi API uploadDocument để gửi file lên server
 * - Thông báo thành công / lỗi bằng message của Ant Design
 * - Chỉ enable nút khi có file và không đang upload
 */
export const UploadButton: React.FC<UploadButtonProps> = ({
  file,
  onSuccess,
  disabled = false,
}) => {
  // Trạng thái đang upload (dùng để hiển thị loading và disable nút)
  const [isUploading, setIsUploading] = useState(false);

  /**
   * Xử lý khi người dùng nhấn nút "Kiểm Tra Đạo Văn"
   * - Kiểm tra file tồn tại
   * - Gọi API upload
   * - Thông báo kết quả
   * - Gọi callback onSuccess nếu thành công
   */
  const handleClick = async () => {
    // Chưa chọn file → cảnh báo
    if (!file) {
      message.warning('Vui lòng chọn file trước');
      return;
    }

    // Bắt đầu quá trình upload
    setIsUploading(true);

    try {
      // Gọi API upload file
      const response = await uploadDocument(file);

      // Thành công → thông báo và truyền job_id cho parent component
      message.success('Kiểm tra hoàn tất!');
      onSuccess(response.job_id);
    } catch (error: any) {
      // Xử lý lỗi
      console.error('Upload error:', error);

      // Lấy thông báo lỗi từ server (nếu có) hoặc fallback về message mặc định
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'Lỗi khi kiểm tra';

      message.error(errorMessage);
    } finally {
      // Luôn kết thúc trạng thái loading dù thành công hay thất bại
      setIsUploading(false);
    }
  };

  return (
    <Button
      type="primary"
      size="large"
      // Icon thay đổi theo trạng thái
      icon={isUploading ? <LoadingOutlined /> : <CheckCircleOutlined />}
      // Disable nút nếu: prop disabled, đang upload, hoặc chưa có file
      disabled={disabled || isUploading || !file}
      // Hiển thị loading spinner của Antd khi đang upload
      loading={isUploading}
      onClick={handleClick}
    >
      {/* Text nút thay đổi theo trạng thái */}
      {isUploading ? 'Đang kiểm tra...' : 'Kiểm Tra Đạo Văn'}
    </Button>
  );
};