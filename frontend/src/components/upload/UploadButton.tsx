import React, { useState } from 'react';
import { Button, message } from 'antd';
import { CheckCircleOutlined, LoadingOutlined } from '@ant-design/icons';
import { uploadDocument } from '../../services/api';

interface UploadButtonProps {
    file: File | null;
    onSuccess: (jobId: string) => void;
    disabled?: boolean;
}

export const UploadButton: React.FC<UploadButtonProps> = ({
    file,
    onSuccess,
    disabled = false
}) => {
    const [isUploading, setIsUploading] = useState(false);

    const handleClick = async () => {
        if (!file) {
            message.warning('Vui lòng chọn file trước');
            return;
        }

        setIsUploading(true);

        try {
            const response = await uploadDocument(file);
            message.success('Kiểm tra hoàn tất!');
            onSuccess(response.job_id);
        } catch (error: any) {
            console.error('Upload error:', error);
            const errorMessage = error.response?.data?.detail || error.message || 'Lỗi khi kiểm tra';
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
            {isUploading ? 'Đang kiểm tra...' : 'Kiểm Tra Đạo Văn'}
        </Button>
    );
};
