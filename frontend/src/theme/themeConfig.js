// src/theme/themeConfig.js

/**
 * Cấu hình theme toàn cục cho Ant Design
 * - Định nghĩa các token màu sắc, border radius... dùng chung toàn ứng dụng
 * - Các màu chính được chọn để phù hợp với mức độ tương đồng (success/warning/error)
 */
export const themeConfig = {
  token: {
    // Màu chính (primary) - dùng cho button, link, các thành phần nổi bật
    colorPrimary: '#1890ff',

    // Màu thành công - dùng cho similarity < 30% (an toàn)
    colorSuccess: '#52c41a',

    // Màu cảnh báo - dùng cho similarity 30-60% (cần xem xét)
    colorWarning: '#faad14',

    // Màu lỗi - dùng cho similarity > 60% (nguy cơ cao)
    colorError: '#ff4d4f',

    // Màu nền container chính (card, table...)
    colorBgContainer: '#ffffff',

    // Màu nền layout tổng thể (body, sider...)
    colorBgLayout: '#f5f5f5',

    // Màu chữ chính
    colorText: '#262626',

    // Màu chữ phụ (secondary text, hint...)
    colorTextSecondary: '#8c8c8c',

    // Độ bo góc mặc định cho các thành phần (button, card, input...)
    borderRadius: 8,
  },
};

/**
 * Hàm helper: trả về màu sắc tương ứng với mức độ tương đồng
 * - Dùng để tô màu Progress, Tag, icon... đồng bộ toàn ứng dụng
 *
 * @param {number} similarity - Giá trị tương đồng (0.0 → 1.0)
 * @returns {string} Màu hex (#rrggbb)
 */
export const getSimilarityColor = (similarity) => {
  if (similarity < 0.3) return '#52c41a';   // Xanh - Thấp
  if (similarity < 0.6) return '#faad14';   // Vàng - Trung bình
  return '#ff4d4f';                         // Đỏ - Cao
};

/**
 * Hàm helper: trả về thông tin mức độ tương đồng (dùng cho Tag, text, level)
 * - Trả về object chứa level (low/medium/high), text hiển thị, và color tag của Antd
 *
 * @param {number} similarity - Giá trị tương đồng (0.0 → 1.0)
 * @returns {{ level: string, text: string, color: 'success'|'warning'|'error' }}
 */
export const getSimilarityLevel = (similarity) => {
  if (similarity < 0.3) {
    return { level: 'low', text: 'Thấp', color: 'success' };
  }
  if (similarity < 0.6) {
    return { level: 'medium', text: 'Trung bình', color: 'warning' };
  }
  return { level: 'high', text: 'Cao', color: 'error' };
};