import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance with default config
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Unauthorized - clear token and redirect to login
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// API Methods

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

// Upload document and check plagiarism
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

export const uploadDocument = async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    // Call the new plagiarism check endpoint
    const response = await apiClient.post<PlagiarismCheckResult>('/plagiarism/check', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });

    // Convert response to expected format
    // Store result in localStorage for result page
    localStorage.setItem('plagiarism_result', JSON.stringify(response.data));

    return {
        job_id: 'direct-check-' + Date.now(),
        message: response.data.is_plagiarized ?
            `Phát hiện đạo văn ${response.data.overall_similarity}%` :
            'Kiểm tra hoàn tất'
    };
};

// Get plagiarism result from localStorage (for direct check)
export const getPlagiarismResult = (): PlagiarismCheckResult | null => {
    const result = localStorage.getItem('plagiarism_result');
    return result ? JSON.parse(result) : null;
};

// Get job status
export const getJobStatus = async (jobId: string): Promise<JobStatusResponse> => {
    const response = await apiClient.get<JobStatusResponse>(`/jobs/${jobId}/status`);
    return response.data;
};

// Get comparison result
export const getComparisonResult = async (queryId: string): Promise<ComparisonResult> => {
    const response = await apiClient.get<ComparisonResult>(`/comparisons/${queryId}`);
    return response.data;
};

// Get comparison history
export const getComparisonHistory = async (
    page: number = 1,
    pageSize: number = 10
): Promise<{ items: HistoryItem[]; total: number }> => {
    const response = await apiClient.get('/plagiarism/history', {
        params: { page, page_size: pageSize },
    });
    return response.data;
};

// Get document content for diff view
export const getDocumentContent = async (documentId: string): Promise<{ content: string }> => {
    const response = await apiClient.get(`/documents/${documentId}/content`);
    return response.data;
};

// Delete comparison
export const deleteComparison = async (queryId: string): Promise<void> => {
    await apiClient.delete(`/plagiarism/history/${queryId}`);
};

// Download history file
export const downloadHistoryFile = async (itemId: string, filename: string): Promise<void> => {
    const response = await apiClient.get(`/plagiarism/history/${itemId}/download`, {
        responseType: 'blob',
    });

    // Create blob link to download
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
};

// Health check
export const healthCheck = async (): Promise<{ status: string }> => {
    const response = await apiClient.get('/health');
    return response.data;
};

export default apiClient;
