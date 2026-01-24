import React, { useState } from 'react';
import { Upload, Card } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { useFileValidation } from '../../hooks/useFileValidation';
import type { UploadProps } from 'antd';

const { Dragger } = Upload;

// Định nghĩa props cho component FileUploader
interface FileUploaderProps {
  // Hàm callback khi người dùng chọn file hợp lệ
  onFileSelect: (file: File) => void;

  // Trạng thái vô hiệu hóa component (disabled)
  disabled?: boolean;
}

/**
 * Component cho phép người dùng upload file bằng cách kéo thả hoặc click
 * - Sử dụng Ant Design Dragger (Upload.Dragger)
 * - Chỉ cho phép 1 file duy nhất
 * - Kiểm tra validation file qua hook useFileValidation
 * - Không tự động upload lên server (chỉ chọn file và gọi callback)
 */
export const FileUploader: React.FC<FileUploaderProps> = ({
  onFileSelect,
  disabled = false,
}) => {
  // Danh sách file (chỉ lưu 1 file vì multiple: false)
  const [fileList, setFileList] = useState<any[]>([]);

  // Hook validation file (kiểm tra loại file, kích thước, v.v.)
  const { validate } = useFileValidation();

  // Cấu hình props cho Upload.Dragger
  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,                  // Chỉ cho phép 1 file
    fileList,                         // Danh sách file hiển thị
    accept: '.pdf,.docx,.txt,.tex',   // Các loại file được chấp nhận
    // Hàm chạy trước khi upload (client-side validation)
    beforeUpload: (file) => {
      // Kiểm tra file có hợp lệ không
      if (!validate(file)) {
        return Upload.LIST_IGNORE; // Bỏ qua file không hợp lệ
      }

      // Lưu file vào state và gọi callback
      setFileList([file]);
      onFileSelect(file);

      return false; // Ngăn tự động upload lên server
    },
    // Xử lý khi xóa file khỏi danh sách
    onRemove: () => {
      setFileList([]);
    },
    disabled, // Vô hiệu hóa nếu prop disabled = true
  };

  return (
    <Card>
      <Dragger {...uploadProps}>
        {/* Icon đại diện */}
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        {/* Hướng dẫn chính */}
        <p className="ant-upload-text">Click hoặc kéo thả file vào đây</p>
        {/* Hướng dẫn chi tiết */}
        <p className="ant-upload-hint">
          Hỗ trợ: PDF, DOCX, TXT, TEX (tối đa 20MB)
        </p>
      </Dragger>
    </Card>
  );
};