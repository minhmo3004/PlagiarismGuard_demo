import React from 'react';
import { Empty, Button } from 'antd';
import { FileSearchOutlined, HistoryOutlined, InboxOutlined } from '@ant-design/icons';

// Các loại empty state được hỗ trợ
type EmptyStateType = 'no-results' | 'no-history' | 'no-matches' | 'upload';

// Props của component
interface EmptyStateProps {
  /**
   * Loại trạng thái trống cần hiển thị
   * - no-results: Chưa có kết quả kiểm tra
   * - no-history: Chưa có lịch sử kiểm tra
   * - no-matches: Không phát hiện đạo văn
   * - upload: Mời upload tài liệu
   */
  type: EmptyStateType;

  /**
   * Hàm được gọi khi người dùng nhấn nút hành động (nếu có)
   * Chỉ hiển thị nút khi type là 'no-results' hoặc 'no-history'
   */
  onAction?: () => void;
}

// Cấu hình cho từng loại empty state
// Dùng object này để dễ dàng thêm/sửa loại trạng thái mới sau này
const emptyConfigs: Record<EmptyStateType, {
  icon: React.ReactNode;
  title: string;
  description: string;
  actionText: string | null;
}> = {
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
    // Icon màu xanh → tạo cảm giác tích cực
    icon: <FileSearchOutlined style={{ fontSize: 48, color: '#52c41a' }} />,
    title: 'Không phát hiện đạo văn! 🎉',
    description: 'Tài liệu của bạn không trùng khớp với bất kỳ tài liệu nào trong cơ sở dữ liệu',
    actionText: null, // Không cần nút hành động
  },

  'upload': {
    // Icon màu xanh Ant → phù hợp với khu vực upload
    icon: <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />,
    title: 'Chọn tài liệu để kiểm tra',
    description: 'Kéo thả hoặc click để chọn file (PDF, DOCX, TXT)',
    actionText: null, // Không cần nút (thường dùng kết hợp với Dropzone)
  },
};

/**
 * Component hiển thị trạng thái trống (Empty State) trong các trang
 * như kết quả kiểm tra, lịch sử, hoặc khu vực upload.
 */
export const EmptyState: React.FC<EmptyStateProps> = ({ type, onAction }) => {
  // Lấy cấu hình tương ứng với type được truyền vào
  const config = emptyConfigs[type];

  return (
    <Empty
      // Sử dụng icon tùy chỉnh thay vì hình mặc định của Antd
      image={config.icon}
      // Nội dung mô tả được tùy chỉnh bằng div + h3 + p
      description={
        <div style={{ textAlign: 'center' }}>
          <h3 style={{ marginBottom: 8, fontSize: 20, fontWeight: 500 }}>
            {config.title}
          </h3>
          <p style={{ color: '#8c8c8c', margin: 0 }}>
            {config.description}
          </p>
        </div>
      }
    >
      {/* Chỉ hiển thị nút khi có actionText VÀ có hàm onAction */}
      {config.actionText && onAction && (
        <Button type="primary" size="large" onClick={onAction}>
          {config.actionText}
        </Button>
      )}
    </Empty>
  );
};