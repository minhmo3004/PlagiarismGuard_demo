import React from 'react';
import ReactDiffViewer from 'react-diff-viewer';
import { Empty, Spin } from 'antd';

// Định nghĩa props cho component DiffViewer
interface DiffViewerProps {
  // Nội dung tài liệu người dùng upload (hiển thị bên phải - "new value")
  queryText: string | null | undefined;

  // Nội dung tài liệu nguồn / tài liệu tham chiếu (hiển thị bên trái - "old value")
  sourceText: string | null | undefined;

  // Tiêu đề bên trái (mặc định: "Tài liệu nguồn")
  leftTitle?: string;

  // Tiêu đề bên phải (mặc định: "Tài liệu của bạn")
  rightTitle?: string;

  // Trạng thái đang tải dữ liệu (hiển thị spinner nếu true)
  isLoading?: boolean;
}

/**
 * Component hiển thị so sánh sự khác biệt (diff) giữa hai đoạn văn bản
 * Sử dụng thư viện react-diff-viewer để hiển thị dạng side-by-side (split view)
 */
export const DiffViewer: React.FC<DiffViewerProps> = ({
  queryText,
  sourceText,
  leftTitle = 'Tài liệu nguồn',
  rightTitle = 'Tài liệu của bạn',
  isLoading = false,
}) => {
  // Trường hợp đang tải dữ liệu → hiển thị spinner
  if (isLoading) {
    return (
      <div className="diff-viewer-loading">
        <Spin size="large" tip="Đang tải nội dung..." />
      </div>
    );
  }

  // Trường hợp không có nội dung nào để so sánh → hiển thị empty state
  if (!queryText && !sourceText) {
    return (
      <Empty
        description="Không có nội dung để so sánh"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    );
  }

  // Xử lý an toàn: chuyển null/undefined thành chuỗi rỗng để tránh lỗi
  const safeQueryText = queryText || '';
  const safeSourceText = sourceText || '';

  return (
    <ReactDiffViewer
      // Văn bản bên trái (tài liệu nguồn - old)
      oldValue={safeSourceText}
      // Văn bản bên phải (tài liệu người dùng - new)
      newValue={safeQueryText}
      
      // Hiển thị hai cột song song (split view)
      splitView={true}
      
      // Tiêu đề hai bên
      leftTitle={leftTitle}
      rightTitle={rightTitle}
      
      // Sử dụng theme sáng
      useDarkTheme={false}
      
      // Hiển thị toàn bộ nội dung (không chỉ phần khác biệt)
      showDiffOnly={false}
      
      // Tùy chỉnh màu sắc cho theme sáng
      styles={{
        variables: {
          light: {
            diffViewerBackground: '#fff',           // Nền chính
            addedBackground: '#e6ffed',             // Nền phần được thêm
            removedBackground: '#ffeef0',           // Nền phần bị xóa
            wordAddedBackground: '#acf2bd',         // Nền từ được thêm
            wordRemovedBackground: '#fdb8c0',       // Nền từ bị xóa
          },
        },
      }}
    />
  );
};