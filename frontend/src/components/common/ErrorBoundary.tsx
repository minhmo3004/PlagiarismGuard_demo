import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button } from 'antd';

// Props của ErrorBoundary
interface Props {
  /** Nội dung con cần được bảo vệ bởi ErrorBoundary */
  children: ReactNode;

  /** (Tùy chọn) Giao diện tùy chỉnh thay thế khi có lỗi, nếu không cung cấp sẽ dùng mặc định */
  fallback?: ReactNode;
}

// State nội bộ để theo dõi lỗi
interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error Boundary component (dùng class component vì React chưa hỗ trợ hook cho Error Boundary)
 * 
 * - Bắt lỗi render ở các component con bên trong
 * - Hiển thị giao diện lỗi thân thiện thay vì làm trắng trang
 * - Hỗ trợ log lỗi và hiển thị chi tiết trong môi trường development
 * - Có nút "Tải lại trang" và "Về trang chủ"
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  /**
   * Cập nhật state để render giao diện fallback khi có lỗi
   * Chạy trước componentDidCatch
   */
  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true };
  }

  /**
   * Bắt lỗi và lưu thông tin chi tiết
   * Thường dùng để log lỗi lên server (ở đây chỉ console.error)
   */
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  /**
   * Reset state boundary và reload trang để khôi phục ứng dụng
   */
  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
    window.location.reload();
  };

  render() {
    // Nếu không có lỗi → render bình thường các component con
    if (!this.state.hasError) {
      return this.props.children;
    }

    // Có lỗi → hiển thị fallback tùy chỉnh (nếu có) hoặc giao diện mặc định
    if (this.props.fallback) {
      return this.props.fallback;
    }

    // Giao diện lỗi mặc định (dùng Ant Design Result)
    return (
      <div style={{ padding: '60px 20px', textAlign: 'center', minHeight: '60vh' }}>
        <Result
          status="error"
          title="Đã xảy ra lỗi"
          subTitle="Xin lỗi, ứng dụng gặp sự cố không mong muốn. Vui lòng thử lại hoặc liên hệ hỗ trợ."
          extra={[
            <Button 
              type="primary" 
              size="large" 
              key="reload" 
              onClick={this.handleReset}
            >
              Tải lại trang
            </Button>,
            <Button 
              size="large" 
              key="home" 
              onClick={() => window.location.href = '/'}
            >
              Về trang chủ
            </Button>,
          ]}
        >
          {/* Chỉ hiển thị chi tiết lỗi khi đang ở môi trường development */}
          {process.env.NODE_ENV === 'development' && this.state.error && (
            <div style={{ marginTop: 24, textAlign: 'left', maxWidth: 800, marginLeft: 'auto', marginRight: 'auto' }}>
              <details style={{ whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: 16, borderRadius: 8 }}>
                <summary style={{ cursor: 'pointer', fontWeight: 500 }}>
                  Chi tiết lỗi (chỉ hiển thị ở development mode)
                </summary>
                <div style={{ marginTop: 12 }}>
                  <p style={{ margin: '8px 0', fontWeight: 500 }}>Lỗi:</p>
                  <pre style={{ background: '#fff', padding: 12, border: '1px solid #eee', borderRadius: 4 }}>
                    {this.state.error.toString()}
                  </pre>
                  
                  <p style={{ margin: '16px 0 8px', fontWeight: 500 }}>Component Stack:</p>
                  <pre style={{ background: '#fff', padding: 12, border: '1px solid #eee', borderRadius: 4 }}>
                    {this.state.errorInfo?.componentStack || 'Không có thông tin stack'}
                  </pre>
                </div>
              </details>
            </div>
          )}
        </Result>
      </div>
    );
  }
}