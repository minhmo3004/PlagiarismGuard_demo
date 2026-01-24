import { message } from 'antd';

// Kết quả kiểm tra tính hợp lệ của file
export interface ValidationResult {
  // File có hợp lệ hay không
  valid: boolean;

  // Thông báo lỗi cụ thể (nếu valid = false)
  error?: string;
}

// Các phần mở rộng file được chấp nhận
const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.tex'];

// Giới hạn kích thước file tối đa: 20MB (tính bằng bytes)
const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20MB

/**
 * Hàm kiểm tra tính hợp lệ của file (pure function, không hiển thị thông báo)
 * Kiểm tra theo thứ tự: tồn tại → phần mở rộng → kích thước → file rỗng
 *
 * @param file - Đối tượng File cần kiểm tra
 * @returns ValidationResult - { valid: true/false, error?: string }
 */
export const validateFile = (file: File): ValidationResult => {
  // Kiểm tra file có tồn tại không
  if (!file) {
    return { valid: false, error: 'Vui lòng chọn file' };
  }

  // Kiểm tra phần mở rộng file (dựa trên tên file)
  const extension = '.' + file.name.split('.').pop()?.toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(extension)) {
    return {
      valid: false,
      error: `Định dạng không hỗ trợ. Chỉ chấp nhận: ${ALLOWED_EXTENSIONS.join(', ')}`
    };
  }

  // Kiểm tra kích thước file
  if (file.size > MAX_FILE_SIZE) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
    return {
      valid: false,
      error: `File quá lớn (${sizeMB}MB). Tối đa 20MB`
    };
  }

  // Kiểm tra file có nội dung không
  if (file.size === 0) {
    return { valid: false, error: 'File rỗng' };
  }

  // File hợp lệ
  return { valid: true };
};

/**
 * Custom hook cung cấp hàm validate file kèm hiển thị thông báo lỗi
 * Sử dụng trong component (thường kết hợp với Upload / FileUploader)
 *
 * @returns {
 *   validate: (file: File) => boolean,          // Trả về true/false + tự show message.error nếu lỗi
 *   validateFile: (file: File) => ValidationResult  // Hàm pure, không show message
 * }
 */
export const useFileValidation = () => {
  /**
   * Hàm validate tiện lợi cho UI: kiểm tra file và tự động hiển thị thông báo lỗi nếu không hợp lệ
   * @returns true nếu hợp lệ, false nếu không hợp lệ (và đã show message.error)
   */
  const validate = (file: File): boolean => {
    const result = validateFile(file);
    if (!result.valid) {
      message.error(result.error);
      return false;
    }
    return true;
  };

  return {
    validate,           // Dùng trong onChange, beforeUpload...
    validateFile,       // Dùng khi cần kiểm tra mà không muốn hiển thị thông báo ngay
  };
};