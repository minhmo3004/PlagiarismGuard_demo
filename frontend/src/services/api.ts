import axios from 'axios';

// URL cơ sở của backend API (lấy từ biến môi trường hoặc fallback về localhost)
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Tạo instance axios với cấu hình mặc định
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor cho request: tự động thêm Bearer token nếu có
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor cho response: xử lý lỗi 401 (Unauthorized)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Nếu nhận lỗi 401 → xóa token/user và chuyển hướng về trang login
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ──────────────────────────────────────────────────────────────────────────────
// Định nghĩa interface cho các response chính
// ──────────────────────────────────────────────────────────────────────────────

export interface UploadResponse {
  job_id: string;
  message: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: 'pending' | 'processing' | 'done' | 'failed' | 'cancelled';
  progress: number;
  result?: any;
  error?: string;
}

export interface ComparisonResult {
  query_id: string;
  query_name: string;
  overall_similarity: number;
  matches: Array<{
    source_id: string;
    source_name: string;
    similarity: number;
    matched_segments: number;
  }>;
  created_at: string;
}

export interface HistoryItem {
  id: string;
  query_name: string;
  overall_similarity: number;
  matches_count: number;
  created_at: string;
}

export interface PlagiarismCheckResult {
  filename: string;
  is_plagiarized: boolean;
  overall_similarity: number;
  plagiarism_level: 'none' | 'low' | 'medium' | 'high';
  word_count: number;
  processing_time_ms: number;
  corpus_size: number;
  matches: Array<{
    title: string;
    author: string;
    university: string;
    year: number | null;
    similarity: number;
  }>;
}

// ──────────────────────────────────────────────────────────────────────────────
// Các hàm gọi API chính
// ──────────────────────────────────────────────────────────────────────────────

/**
 * Upload file và kiểm tra đạo văn trực tiếp (endpoint /plagiarism/check)
 * - Sử dụng FormData để gửi file
 * - Lưu kết quả vào localStorage để trang result đọc
 * - Trả về object giả lập UploadResponse (vì endpoint này không trả job_id thật)
 */
export const uploadDocument = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<PlagiarismCheckResult>('/plagiarism/check', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  // Lưu kết quả vào localStorage để trang /result đọc
  localStorage.setItem('plagiarism_result', JSON.stringify(response.data));

  return {
    job_id: 'direct-check-' + Date.now(),
    message: response.data.is_plagiarized
      ? `Phát hiện đạo văn ${response.data.overall_similarity}%`
      : 'Kiểm tra hoàn tất',
  };
};

/**
 * Lấy kết quả kiểm tra đạo văn từ localStorage
 * (dùng cho trường hợp kiểm tra trực tiếp không qua job polling)
 */
export const getPlagiarismResult = (): PlagiarismCheckResult | null => {
  const result = localStorage.getItem('plagiarism_result');
  return result ? JSON.parse(result) : null;
};

/**
 * Lấy trạng thái tiến trình của một job (dùng cho polling)
 */
export const getJobStatus = async (jobId: string): Promise<JobStatusResponse> => {
  const response = await apiClient.get<JobStatusResponse>(`/jobs/${jobId}/status`);
  return response.data;
};

/**
 * Lấy chi tiết kết quả so sánh của một query cụ thể
 */
export const getComparisonResult = async (queryId: string): Promise<ComparisonResult> => {
  const response = await apiClient.get<ComparisonResult>(`/comparisons/${queryId}`);
  return response.data;
};

/**
 * Lấy danh sách lịch sử kiểm tra (có phân trang)
 */
export const getComparisonHistory = async (
  page: number = 1,
  pageSize: number = 10
): Promise<{ items: HistoryItem[]; total: number }> => {
  const response = await apiClient.get('/plagiarism/history', {
    params: { page, page_size: pageSize },
  });
  return response.data;
};

/**
 * Lấy nội dung văn bản của một tài liệu (dùng cho diff viewer)
 */
export const getDocumentContent = async (documentId: string): Promise<{ content: string }> => {
  const response = await apiClient.get(`/documents/${documentId}/content`);
  return response.data;
};

/**
 * Xóa một bản ghi lịch sử kiểm tra
 */
export const deleteComparison = async (queryId: string): Promise<void> => {
  await apiClient.delete(`/plagiarism/history/${queryId}`);
};

/**
 * Tải file kết quả kiểm tra về máy (trả về blob)
 */
export const downloadHistoryFile = async (itemId: string, filename: string): Promise<void> => {
  const response = await apiClient.get(`/plagiarism/history/${itemId}/download`, {
    responseType: 'blob',
  });

  // Tạo link tải tự động
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

/**
 * Kiểm tra sức khỏe của backend (health check)
 */
export const healthCheck = async (): Promise<{ status: string }> => {
  const response = await apiClient.get('/health');
  return response.data;
};

export default apiClient;