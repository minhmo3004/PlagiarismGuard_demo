import React from 'react';
import { Empty, Button } from 'antd';
import { FileSearchOutlined, HistoryOutlined, InboxOutlined } from '@ant-design/icons';

type EmptyStateType = 'no-results' | 'no-history' | 'no-matches' | 'upload';

interface EmptyStateProps {
    type: EmptyStateType;
    onAction?: () => void;
}

const emptyConfigs = {
    'no-results': {
        icon: <FileSearchOutlined style={{ fontSize: 48, color: '#bfbfbf' }} />,
        title: 'Chưa có kết quả',
        description: 'Upload tài liệu để bắt đầu kiểm tra đạo văn',
        actionText: 'Upload ngay',
    },
    'no-history': {
        icon: <HistoryOutlined style={{ fontSize: 48, color: '#bfbfbf' }} />,
        title: 'Chưa có lịch sử kiểm tra',
        description: 'Các kết quả kiểm tra của bạn sẽ xuất hiện ở đây',
        actionText: 'Kiểm tra ngay',
    },
    'no-matches': {
        icon: <FileSearchOutlined style={{ fontSize: 48, color: '#52c41a' }} />,
        title: 'Không phát hiện đạo văn! 🎉',
        description: 'Tài liệu của bạn không trùng khớp với bất kỳ tài liệu nào trong cơ sở dữ liệu',
        actionText: null,
    },
    'upload': {
        icon: <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />,
        title: 'Chọn tài liệu để kiểm tra',
        description: 'Kéo thả hoặc click để chọn file (PDF, DOCX, TXT)',
        actionText: null,
    },
};

export const EmptyState: React.FC<EmptyStateProps> = ({ type, onAction }) => {
    const config = emptyConfigs[type];

    return (
        <Empty
            image={config.icon}
            description={
                <div>
                    <h3 style={{ marginBottom: 8 }}>{config.title}</h3>
                    <p style={{ color: '#8c8c8c' }}>{config.description}</p>
                </div>
            }
        >
            {config.actionText && onAction && (
                <Button type="primary" onClick={onAction}>
                    {config.actionText}
                </Button>
            )}
        </Empty>
    );
};
