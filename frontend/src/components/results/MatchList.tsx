import React from 'react';
import { List, Card, Tag, Progress, Button } from 'antd';
import { FileTextOutlined, EyeOutlined } from '@ant-design/icons';

// Định nghĩa cấu trúc của một mục trùng khớp
interface Match {
  // ID của tài liệu nguồn (trong cơ sở dữ liệu)
  source_id: string;

  // Tên/tựa đề của tài liệu nguồn
  source_name: string;

  // Độ tương đồng (0.0 → 1.0)
  similarity: number;

  // Số đoạn văn bản trùng khớp với tài liệu nguồn
  matched_segments: number;
}

// Props của component MatchList
interface MatchListProps {
  // Danh sách các tài liệu trùng khớp
  matches: Match[];

  // Hàm xử lý khi người dùng nhấn "Xem chi tiết" một mục
  onViewDetails?: (match: Match) => void;

  // Trạng thái đang tải dữ liệu (hiển thị loading của List)
  loading?: boolean;
}

/**
 * Hàm helper: trả về Tag màu tương ứng với mức độ tương đồng
 * - < 30%   → màu xanh (Thấp)
 * - < 60%   → màu vàng (Trung bình)
 * - ≥ 60%   → màu đỏ (Cao)
 */
const getSimilarityTag = (similarity: number) => {
  if (similarity < 0.3) {
    return <Tag color="success">Thấp ({Math.round(similarity * 100)}%)</Tag>;
  }
  if (similarity < 0.6) {
    return <Tag color="warning">Trung bình ({Math.round(similarity * 100)}%)</Tag>;
  }
  return <Tag color="error">Cao ({Math.round(similarity * 100)}%)</Tag>;
};

/**
 * Component hiển thị danh sách các tài liệu trùng khớp (Match List)
 * - Hiển thị trong một Card với tiêu đề "Danh sách tài liệu trùng khớp"
 * - Mỗi mục gồm: tên tài liệu, tag mức độ tương đồng, số đoạn trùng, thanh tiến độ
 * - Có nút "Xem chi tiết" (nếu truyền onViewDetails)
 */
export const MatchList: React.FC<MatchListProps> = ({
  matches,
  onViewDetails,
  loading = false,
}) => {
  return (
    <Card title="Danh sách tài liệu trùng khớp">
      <List
        // Hiển thị loading spinner khi đang tải dữ liệu
        loading={loading}
        // Dữ liệu nguồn là mảng matches
        dataSource={matches}
        // Cách render từng item trong danh sách
        renderItem={(match) => (
          <List.Item
            // Các hành động bên phải mỗi item (nút Xem chi tiết)
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
              // Icon đại diện cho tài liệu
              avatar={<FileTextOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
              // Tiêu đề: tên tài liệu nguồn
              title={match.source_name}
              // Mô tả: tag mức độ + số đoạn + thanh tiến độ
              description={
                <div>
                  <div style={{ marginBottom: 8 }}>
                    {getSimilarityTag(match.similarity)}
                    <Tag>{match.matched_segments} đoạn trùng khớp</Tag>
                  </div>
                  <Progress
                    percent={Math.round(match.similarity * 100)}
                    size="small"
                    // Màu thanh tiến độ đồng bộ với mức độ tương đồng
                    strokeColor={
                      match.similarity < 0.3 ? '#52c41a' :
                      match.similarity < 0.6 ? '#faad14' :
                      '#ff4d4f'
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