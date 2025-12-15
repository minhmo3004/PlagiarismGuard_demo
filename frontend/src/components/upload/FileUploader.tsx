import React, { useState } from 'react';
import { Upload, Card } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { useFileValidation } from '../../hooks/useFileValidation';
import type { UploadProps } from 'antd';

const { Dragger } = Upload;

interface FileUploaderProps {
    onFileSelect: (file: File) => void;
    disabled?: boolean;
}

export const FileUploader: React.FC<FileUploaderProps> = ({
    onFileSelect,
    disabled = false
}) => {
    const [fileList, setFileList] = useState<any[]>([]);
    const { validate } = useFileValidation();

    const uploadProps: UploadProps = {
        name: 'file',
        multiple: false,
        fileList,
        accept: '.pdf,.docx,.txt,.tex',
        beforeUpload: (file) => {
            // Client-side validation
            if (!validate(file)) {
                return Upload.LIST_IGNORE;
            }

            setFileList([file]);
            onFileSelect(file);
            return false; // Prevent auto upload
        },
        onRemove: () => {
            setFileList([]);
        },
        disabled,
    };

    return (
        <Card>
            <Dragger {...uploadProps}>
                <p className="ant-upload-drag-icon">
                    <InboxOutlined />
                </p>
                <p className="ant-upload-text">Click hoặc kéo thả file vào đây</p>
                <p className="ant-upload-hint">
                    Hỗ trợ: PDF, DOCX, TXT, TEX (tối đa 20MB)
                </p>
            </Dragger>
        </Card>
    );
};
