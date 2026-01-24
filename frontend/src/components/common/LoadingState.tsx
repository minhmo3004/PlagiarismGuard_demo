import React from 'react';
import { Spin, Progress, Card } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';

// Các kiểu loading được hỗ trợ
type LoadingType = 'spinner' | 'progress' | 'skeleton';

interface LoadingStateProps {
  /**
   * Phần trăm tiến độ (0-100). Chỉ có ý nghĩa khi type = 'progress'
   * Nếu không truyền hoặc undefined → không hiển thị progress
   */
  progress?: number;

  /**
   * Thông báo text hiển thị kèm loading
   * @default "Đang xử lý..."
   */
  message?: string;

  /**
   * Kiểu hiển thị loading
   * - spinner: Biểu tượng quay vòng đơn giản (mặc định)
   * - progress: Vòng tròn tiến độ + phần trăm
   * - skeleton: (chưa implement) có thể dùng cho loading placeholder
   * @default 'spinner'
   */
  type?: LoadingType;
}

/**
 * Component hiển thị trạng thái đang tải (Loading State)
 * Dùng linh hoạt ở nhiều vị trí: toàn trang, trong card, khi upload, xử lý API dài,...
 */
export const LoadingState: React.FC<LoadingStateProps> = ({
  progress,
  message = 'Đang xử lý...',
  type = 'spinner',
}) => {
  // Trường hợp hiển thị progress circle (khi có type 'progress' và progress được truyền)
  if (type === 'progress' && progress !== undefined) {
    return (
      <Card 
        className="loading-card" 
        bordered={false} 
        style={{ background: 'transparent', boxShadow: 'none' }}
      >
        <div style={{ textAlign: 'center', padding: '40px 20px' }}>
          <Progress
            type="circle"
            percent={Math.min(Math.max(Math.round(progress), 0), 100)} // Giới hạn 0-100
            status="active"
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#1890ff',
            }}
            format={(percent) => `${percent}%`}
          />
          <p style={{ marginTop: 16, color: '#8c8c8c', fontSize: 14 }}>
            {message}
          </p>
        </div>
      </Card>
    );
  }

  // Trường hợp mặc định: spinner quay vòng (dùng cho type 'spinner' hoặc bất kỳ type nào khác)
  // Type 'skeleton' chưa được implement → fallback về spinner
  return (
    <div 
      className="loading-spinner" 
      style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '200px' // tránh layout nhảy khi dùng full-page loading
      }}
    >
      <Spin
        indicator={<LoadingOutlined style={{ fontSize: 36, color: '#1890ff' }} spin />}
        tip={message}
        size="large"
      />
    </div>
  );
};