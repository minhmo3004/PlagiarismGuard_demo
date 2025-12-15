import { useState, useEffect, useRef, useCallback } from 'react';
import { getJobStatus } from '../services/api';
import { useToast } from './useToast';

type JobStatus = 'pending' | 'processing' | 'done' | 'failed' | 'cancelled';

interface UseJobPollingResult {
    status: JobStatus;
    progress: number;
    result: any | null;
    error: string | null;
    isLoading: boolean;
    retry: () => void;
}

const POLL_INTERVAL = 2000;      // 2 seconds
const MAX_POLL_TIME = 300000;    // 5 minutes timeout
const MAX_CONSECUTIVE_ERRORS = 3;

export const useJobPolling = (jobId: string | null): UseJobPollingResult => {
    const [status, setStatus] = useState<JobStatus>('pending');
    const [progress, setProgress] = useState(0);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const startTimeRef = useRef<number>(Date.now());
    const consecutiveErrorsRef = useRef<number>(0);
    const { showError } = useToast();

    const resetPolling = useCallback(() => {
        setStatus('pending');
        setProgress(0);
        setResult(null);
        setError(null);
        startTimeRef.current = Date.now();
        consecutiveErrorsRef.current = 0;
    }, []);

    useEffect(() => {
        if (!jobId) return;

        setIsLoading(true);
        resetPolling();

        const pollInterval = setInterval(async () => {
            // ✅ Timeout check
            if (Date.now() - startTimeRef.current > MAX_POLL_TIME) {
                setError('Quá thời gian chờ. Vui lòng thử lại.');
                setStatus('failed');
                setIsLoading(false);
                clearInterval(pollInterval);
                showError('Timeout', 'Quá thời gian chờ xử lý');
                return;
            }

            try {
                const response = await getJobStatus(jobId);

                // ✅ Reset error counter on success
                consecutiveErrorsRef.current = 0;

                setStatus(response.status);
                setProgress(response.progress || 0);

                if (response.status === 'done') {
                    setResult(response.result);
                    setIsLoading(false);
                    clearInterval(pollInterval);
                }
                // ✅ Handle failed status
                else if (response.status === 'failed') {
                    setError(response.error || 'Có lỗi xảy ra khi xử lý');
                    setIsLoading(false);
                    clearInterval(pollInterval);
                    showError('Lỗi xử lý', response.error || 'Không thể hoàn thành kiểm tra');
                }
                // ✅ Handle cancelled status
                else if (response.status === 'cancelled') {
                    setError('Đã hủy');
                    setIsLoading(false);
                    clearInterval(pollInterval);
                }

            } catch (err: any) {
                // ✅ Handle API errors
                consecutiveErrorsRef.current += 1;

                if (consecutiveErrorsRef.current >= MAX_CONSECUTIVE_ERRORS) {
                    setError('Không thể kết nối với server');
                    setStatus('failed');
                    setIsLoading(false);
                    clearInterval(pollInterval);
                    showError('Lỗi kết nối', 'Không thể kết nối với server');
                }
            }
        }, POLL_INTERVAL);

        return () => {
            clearInterval(pollInterval);
            setIsLoading(false);
        };
    }, [jobId, resetPolling, showError]);

    const retry = useCallback(() => {
        if (jobId) {
            resetPolling();
            // Trigger re-poll by updating ref
            startTimeRef.current = Date.now();
        }
    }, [jobId, resetPolling]);

    return { status, progress, result, error, isLoading, retry };
};
