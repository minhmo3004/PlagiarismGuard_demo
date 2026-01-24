import { useState, useEffect, useRef, useCallback } from 'react';
import { getJobStatus } from '../services/api';
import { useToast } from './useToast';

// Các trạng thái công việc có thể có (từ backend)
type JobStatus = 'pending' | 'processing' | 'done' | 'failed' | 'cancelled';

// Kết quả trả về từ hook useJobPolling
interface UseJobPollingResult {
  status: JobStatus;          // Trạng thái hiện tại của job
  progress: number;           // Phần trăm tiến độ (0-100)
  result: any | null;         // Kết quả khi job hoàn thành (done)
  error: string | null;       // Thông báo lỗi (nếu có)
  isLoading: boolean;         // Đang thực hiện polling hay không
  retry: () => void;          // Hàm thử lại polling từ đầu
}

// Cấu hình polling
const POLL_INTERVAL = 2000;           // Khoảng thời gian gọi API (2 giây)
const MAX_POLL_TIME = 300000;         // Thời gian tối đa chờ (5 phút)
const MAX_CONSECUTIVE_ERRORS = 3;     // Số lỗi liên tiếp tối đa trước khi dừng

/**
 * Custom hook quản lý polling trạng thái job (kiểm tra đạo văn, xử lý file, v.v.)
 * - Tự động gọi API getJobStatus định kỳ để cập nhật trạng thái
 * - Xử lý timeout, lỗi liên tiếp, trạng thái done/failed/cancelled
 * - Cung cấp retry khi cần thử lại
 * - Sử dụng toast để thông báo lỗi nghiêm trọng
 *
 * @param jobId - ID của job cần theo dõi (null thì không làm gì)
 * @returns UseJobPollingResult - trạng thái, tiến độ, kết quả, lỗi, retry...
 */
export const useJobPolling = (jobId: string | null): UseJobPollingResult => {
  const [status, setStatus] = useState<JobStatus>('pending');
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Lưu thời gian bắt đầu polling (dùng ref để không gây re-render)
  const startTimeRef = useRef<number>(Date.now());

  // Đếm số lỗi API liên tiếp
  const consecutiveErrorsRef = useRef<number>(0);

  const { showError } = useToast();

  // Reset toàn bộ trạng thái polling về ban đầu
  const resetPolling = useCallback(() => {
    setStatus('pending');
    setProgress(0);
    setResult(null);
    setError(null);
    startTimeRef.current = Date.now();
    consecutiveErrorsRef.current = 0;
  }, []);

  useEffect(() => {
    // Không có jobId → không làm gì
    if (!jobId) return;

    setIsLoading(true);
    resetPolling();

    // Thiết lập interval polling
    const pollInterval = setInterval(async () => {
      // Kiểm tra timeout tổng thể
      if (Date.now() - startTimeRef.current > MAX_POLL_TIME) {
        setError('Quá thời gian chờ. Vui lòng thử lại.');
        setStatus('failed');
        setIsLoading(false);
        clearInterval(pollInterval);
        showError('Timeout', 'Quá thời gian chờ xử lý');
        return;
      }

      try {
        // Gọi API lấy trạng thái job
        const response = await getJobStatus(jobId);

        // Reset bộ đếm lỗi khi gọi thành công
        consecutiveErrorsRef.current = 0;

        setStatus(response.status);
        setProgress(response.progress || 0);

        // Job hoàn thành
        if (response.status === 'done') {
          setResult(response.result);
          setIsLoading(false);
          clearInterval(pollInterval);
        }
        // Job thất bại
        else if (response.status === 'failed') {
          setError(response.error || 'Có lỗi xảy ra khi xử lý');
          setIsLoading(false);
          clearInterval(pollInterval);
          showError('Lỗi xử lý', response.error || 'Không thể hoàn thành kiểm tra');
        }
        // Job bị hủy
        else if (response.status === 'cancelled') {
          setError('Đã hủy');
          setIsLoading(false);
          clearInterval(pollInterval);
        }

      } catch (err: any) {
        // Xử lý lỗi khi gọi API
        consecutiveErrorsRef.current += 1;

        // Nếu lỗi liên tiếp quá nhiều → dừng polling
        if (consecutiveErrorsRef.current >= MAX_CONSECUTIVE_ERRORS) {
          setError('Không thể kết nối với server');
          setStatus('failed');
          setIsLoading(false);
          clearInterval(pollInterval);
          showError('Lỗi kết nối', 'Không thể kết nối với server');
        }
      }
    }, POLL_INTERVAL);

    // Cleanup: dừng polling khi component unmount hoặc jobId thay đổi
    return () => {
      clearInterval(pollInterval);
      setIsLoading(false);
    };
  }, [jobId, resetPolling, showError]);

  // Hàm retry: reset trạng thái và bắt đầu polling lại
  const retry = useCallback(() => {
    if (jobId) {
      resetPolling();
      // Đặt lại thời gian bắt đầu để tránh timeout ngay lập tức
      startTimeRef.current = Date.now();
    }
  }, [jobId, resetPolling]);

  return { status, progress, result, error, isLoading, retry };
};