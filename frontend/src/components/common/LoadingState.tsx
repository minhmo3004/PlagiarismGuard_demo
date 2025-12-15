import React from 'react';
import { Spin, Progress, Card } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';

interface LoadingStateProps {
    progress?: number;
    message?: string;
    type?: 'spinner' | 'progress' | 'skeleton';
}

export const LoadingState: React.FC<LoadingStateProps> = ({
    progress,
    message = 'Đang xử lý...',
    type = 'spinner'
}) => {
    if (type === 'progress' && progress !== undefined) {
        return (
            <Card className="loading-card">
                <div style={{ textAlign: 'center' }}>
                    <Progress
                        type="circle"
                        percent={Math.round(progress)}
                        status="active"
                    />
                    <p style={{ marginTop: 16, color: '#8c8c8c' }}>{message}</p>
                </div>
            </Card>
        );
    }

    return (
        <div className="loading-spinner">
            <Spin
                indicator={<LoadingOutlined style={{ fontSize: 32 }} spin />}
                tip={message}
            />
        </div>
    );
};
