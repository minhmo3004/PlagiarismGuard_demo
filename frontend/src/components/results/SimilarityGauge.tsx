import React from 'react';
import { Card, Progress, Tag } from 'antd';
import { WarningOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';

interface SimilarityGaugeProps {
    similarity: number;
    title?: string;
}

const getSimilarityConfig = (similarity: number) => {
    if (similarity < 0.3) {
        return {
            color: '#52c41a',
            status: 'success' as const,
            level: 'Thấp',
            icon: <CheckCircleOutlined />,
            tagColor: 'success',
        };
    }
    if (similarity < 0.6) {
        return {
            color: '#faad14',
            status: 'normal' as const,
            level: 'Trung bình',
            icon: <WarningOutlined />,
            tagColor: 'warning',
        };
    }
    return {
        color: '#ff4d4f',
        status: 'exception' as const,
        level: 'Cao',
        icon: <CloseCircleOutlined />,
        tagColor: 'error',
    };
};

export const SimilarityGauge: React.FC<SimilarityGaugeProps> = ({
    similarity,
    title = 'Độ tương đồng'
}) => {
    const config = getSimilarityConfig(similarity);
    const percent = Math.round(similarity * 100);

    return (
        <Card>
            <div style={{ textAlign: 'center' }}>
                <h3>{title}</h3>
                <Progress
                    type="circle"
                    percent={percent}
                    strokeColor={config.color}
                    status={config.status}
                    format={(percent) => (
                        <div>
                            <div style={{ fontSize: 32, fontWeight: 'bold' }}>{percent}%</div>
                            <Tag color={config.tagColor} icon={config.icon}>
                                {config.level}
                            </Tag>
                        </div>
                    )}
                    width={180}
                />
                <p style={{ marginTop: 16, color: '#8c8c8c' }}>
                    {similarity < 0.3 && 'Tài liệu an toàn'}
                    {similarity >= 0.3 && similarity < 0.6 && 'Cần xem xét'}
                    {similarity >= 0.6 && 'Nguy cơ đạo văn cao'}
                </p>
            </div>
        </Card>
    );
};
