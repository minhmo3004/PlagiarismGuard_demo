import React from 'react';
import { Card, Progress, Tag } from 'antd';
import { WarningOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';

// Định nghĩa props cho component SimilarityGauge
interface SimilarityGaugeProps {
  // Giá trị độ tương đồng (từ 0.0 đến 1.0)
  similarity: number;

  // Tiêu đề hiển thị (mặc định: "Độ tương đồng")
  title?: string;
}

/**
 * Hàm helper: trả về cấu hình màu sắc, icon, trạng thái và mức độ dựa trên giá trị similarity
 * - < 30%   → Thấp (xanh, thành công)
 * - < 60%   → Trung bình (vàng, cảnh báo)
 * - ≥ 60%   → Cao (đỏ, lỗi/nguy hiểm)
 */
const getSimilarityConfig = (similarity: number) => {
  if (similarity < 0.3) {
    return {
      color: '#52c41a',           // Xanh lá
      status: 'success' as const,
      level: 'Thấp',
      icon: <CheckCircleOutlined />,
      tagColor: 'success',
    };
  }
  if (similarity < 0.6) {
    return {
      color: '#faad14',           // Vàng
      status: 'normal' as const,
      level: 'Trung bình',
      icon: <WarningOutlined />,
      tagColor: 'warning',
    };
  }
  return {
    color: '#ff4d4f',           // Đỏ
    status: 'exception' as const,
    level: 'Cao',
    icon: <CloseCircleOutlined />,
    tagColor: 'error',
  };
};

/**
 * Component hiển thị mức độ tương đồng (Similarity Gauge) dạng vòng tròn
 * - Sử dụng Progress circle của Ant Design
 * - Hiển thị phần trăm lớn ở giữa + Tag mức độ + mô tả trạng thái
 * - Màu sắc và icon thay đổi theo mức độ tương đồng
 */
export const SimilarityGauge: React.FC<SimilarityGaugeProps> = ({
  similarity,
  title = 'Độ tương đồng',
}) => {
  // Lấy cấu hình tương ứng với giá trị similarity
  const config = getSimilarityConfig(similarity);

  // Chuyển similarity thành phần trăm (0-100) và làm tròn
  const percent = Math.round(similarity * 100);

  return (
    <Card>
      <div style={{ textAlign: 'center' }}>
        {/* Tiêu đề */}
        <h3>{title}</h3>

        {/* Vòng tròn tiến độ hiển thị phần trăm */}
        <Progress
          type="circle"
          percent={percent}
          strokeColor={config.color}
          status={config.status}
          width={180}
          // Tùy chỉnh nội dung bên trong vòng tròn
          format={(percent) => (
            <div>
              {/* Phần trăm lớn, đậm */}
              <div style={{ fontSize: 32, fontWeight: 'bold' }}>{percent}%</div>
              {/* Tag hiển thị mức độ + icon */}
              <Tag color={config.tagColor} icon={config.icon}>
                {config.level}
              </Tag>
            </div>
          )}
        />

        {/* Mô tả trạng thái (dưới vòng tròn) */}
        <p style={{ marginTop: 16, color: '#8c8c8c' }}>
          {similarity < 0.3 && 'Tài liệu an toàn'}
          {similarity >= 0.3 && similarity < 0.6 && 'Cần xem xét'}
          {similarity >= 0.6 && 'Nguy cơ đạo văn cao'}
        </p>
      </div>
    </Card>
  );
};