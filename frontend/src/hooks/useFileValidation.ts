import { message } from 'antd';

export interface ValidationResult {
    valid: boolean;
    error?: string;
}


const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.tex'];
const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20MB

export const validateFile = (file: File): ValidationResult => {
    // ✅ Check file exists
    if (!file) {
        return { valid: false, error: 'Vui lòng chọn file' };
    }

    // ✅ Check file type
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
        return {
            valid: false,
            error: `Định dạng không hỗ trợ. Chấp nhận: ${ALLOWED_EXTENSIONS.join(', ')}`
        };
    }

    // ✅ Check file size
    if (file.size > MAX_FILE_SIZE) {
        const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
        return {
            valid: false,
            error: `File quá lớn (${sizeMB}MB). Tối đa 20MB`
        };
    }

    // ✅ Check if file is empty
    if (file.size === 0) {
        return { valid: false, error: 'File rỗng' };
    }

    return { valid: true };
};

// Hook for validation
export const useFileValidation = () => {
    const validate = (file: File): boolean => {
        const result = validateFile(file);
        if (!result.valid) {
            message.error(result.error);
            return false;
        }
        return true;
    };

    return { validate, validateFile };
};
