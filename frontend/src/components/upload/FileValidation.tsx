import { message } from 'antd';

// Kết quả kiểm tra file
export interface ValidationResult {
  // File có hợp lệ hay không
  valid: boolean;

  // Thông báo lỗi (nếu valid = false)
  error?: string;
}

// Danh sách MIME types được chấp nhận
const ALLOWED_TYPES = [
  'application/pdf',                                    // PDF
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // DOCX
  'text/plain',                                         // TXT
  'application/x-tex',                                  // TeX / LaTeX
];

// Danh sách phần mở rộng file được chấp nhận (dùng để kiểm tra tên file)
const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.tex'];

// Giới hạn kích thước file: 20MB
const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20MB tính bằng bytes

/**
 * Hàm kiểm tra tính hợp lệ của file trước khi xử lý
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

  // Kiểm tra file có rỗng không
  if (file.size === 0) {
    return { valid: false, error: 'File rỗng' };
  }

  // File hợp lệ
  return { valid: true };
};

/**
 * Object export tiện lợi, chứa hàm validate và các hằng số cấu hình
 * Có thể dùng để import một lần duy nhất: import { FileValidation } from '...';
 */
export const FileValidation = {
  validateFile,
  ALLOWED_EXTENSIONS,
  MAX_FILE_SIZE,
};