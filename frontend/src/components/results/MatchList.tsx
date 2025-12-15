import React from 'react';
import { List, Card, Tag, Progress, Button } from 'antd';
import { FileTextOutlined, EyeOutlined } from '@ant-design/icons';

interface Match {
    source_id: string;
    source_name: string;
    similarity: number;
    matched_segments: number;
}

interface MatchListProps {
    matches: Match[];
    onViewDetails?: (match: Match) => void;
    loading?: boolean;
}

const getSimilarityTag = (similarity: number) => {
    if (similarity < 0.3) {
        return <Tag color="success">Thấp ({Math.round(similarity * 100)}%)</Tag>;
    }
    if (similarity < 0.6) {
        return <Tag color="warning">Trung bình ({Math.round(similarity * 100)}%)</Tag>;
    }
    return <Tag color="error">Cao ({Math.round(similarity * 100)}%)</Tag>;
};

export const MatchList: React.FC<MatchListProps> = ({
    matches,
    onViewDetails,
    loading = false
}) => {
    return (
        <Card title="Danh sách tài liệu trùng khớp">
            <List
                loading={loading}
                dataSource={matches}
                renderItem={(match) => (
                    <List.Item
                        actions={[
                            onViewDetails && (
                                <Button
                                    type="link"
                                    icon={<EyeOutlined />}
                                    onClick={() => onViewDetails(match)}
                                >
                                    Xem chi tiết
                                </Button>
                            ),
                        ]}
                    >
                        <List.Item.Meta
                            avatar={<FileTextOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
                            title={match.source_name}
                            description={
                                <div>
                                    <div style={{ marginBottom: 8 }}>
                                        {getSimilarityTag(match.similarity)}
                                        <Tag>{match.matched_segments} đoạn trùng khớp</Tag>
                                    </div>
                                    <Progress
                                        percent={Math.round(match.similarity * 100)}
                                        size="small"
                                        strokeColor={
                                            match.similarity < 0.3 ? '#52c41a' :
                                                match.similarity < 0.6 ? '#faad14' : '#ff4d4f'
                                        }
                                    />
                                </div>
                            }
                        />
                    </List.Item>
                )}
            />
        </Card>
    );
};
