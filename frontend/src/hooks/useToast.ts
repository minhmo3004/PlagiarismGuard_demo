import { message, notification } from 'antd';

// Các loại toast/notification được hỗ trợ
type ToastType = 'success' | 'error' | 'info' | 'warning';

/**
 * Custom hook cung cấp các hàm hiển thị thông báo (toast & notification)
 * - Sử dụng message của Ant Design cho toast đơn giản (xuất hiện ở giữa dưới màn hình)
 * - Sử dụng notification của Ant Design cho thông báo có tiêu đề + mô tả (góc trên phải)
 * - Các hàm được đặt tên ngắn gọn, dễ dùng trong component
 */
export const useToast = () => {
  /**
   * Hàm chung hiển thị toast đơn giản (không có tiêu đề)
   * @param type - Loại toast: success | error | info | warning
   * @param content - Nội dung thông báo
   */
  const showToast = (type: ToastType, content: string) => {
    message[type](content);
  };

  /**
   * Hàm chung hiển thị notification có tiêu đề và mô tả
   * - Vị trí: góc trên phải màn hình
   * - Tự động biến mất sau 4.5 giây
   *
   * @param type - Loại notification
   * @param title - Tiêu đề thông báo
   * @param description - Mô tả chi tiết (tùy chọn)
   */
  const showNotification = (
    type: ToastType,
    title: string,
    description?: string
  ) => {
    notification[type]({
      message: title,
      description,
      placement: 'topRight',
      duration: 4.5,
    });
  };

  return {
    // Toast đơn giản (chỉ nội dung, không tiêu đề)
    success: (content: string) => showToast('success', content),
    error: (content: string) => showToast('error', content),
    info: (content: string) => showToast('info', content),
    warning: (content: string) => showToast('warning', content),

    // Notification có tiêu đề + mô tả (dùng khi cần thông tin chi tiết hơn)
    showSuccess: (title: string, desc?: string) => showNotification('success', title, desc),
    showError: (title: string, desc?: string) => showNotification('error', title, desc),
    showInfo: (title: string, desc?: string) => showNotification('info', title, desc),
    showWarning: (title: string, desc?: string) => showNotification('warning', title, desc),
  };
};