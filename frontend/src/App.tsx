import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, Layout, Menu } from 'antd';
import {
  HomeOutlined,
  UploadOutlined,
  HistoryOutlined,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { HomePage } from './pages/HomePage';
import { UploadPage } from './pages/UploadPage';
import { ResultPage } from './pages/ResultPage';
import { HistoryPage } from './pages/HistoryPage';
import { LoginPage } from './pages/LoginPage';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { useAuth } from './hooks/useAuth';
import './App.css';

const { Header, Footer } = Layout;

// Cấu hình theme cho Ant Design (màu sắc, font, border... dùng chung toàn app)
const themeConfig = {
  token: {
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    colorBgContainer: '#ffffff',
    colorBgLayout: '#f5f5f5',
    colorText: '#262626',
    colorTextSecondary: '#8c8c8c',
    borderRadius: 8,
  },
};

/**
 * Component bảo vệ route (Protected Route)
 * - Kiểm tra trạng thái auth từ useAuth
 * - Nếu đang load → hiển thị loading
 * - Nếu chưa đăng nhập → redirect về /login
 */
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

/**
 * Layout chính của ứng dụng (AppLayout)
 * - Bao gồm Header (logo + menu trái + menu phải với user/logout)
 * - Nội dung con (children) bọc trong ErrorBoundary
 * - Footer dưới cùng
 */
const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, user, logout } = useAuth();
  const location = window.location.pathname;
  const current = location === '/' ? 'home' : location.substring(1);

  // Menu trái: các mục chính (Trang chủ, Kiểm tra, Lịch sử)
  const menuItems = [
    {
      key: 'home',
      icon: <HomeOutlined />,
      label: 'Trang chủ',
      onClick: () => window.location.href = '/',
    },
    {
      key: 'upload',
      icon: <UploadOutlined />,
      label: 'Kiểm tra',
      onClick: () => window.location.href = '/upload',
    },
    {
      key: 'history',
      icon: <HistoryOutlined />,
      label: 'Lịch sử',
      onClick: () => window.location.href = '/history',
    },
  ];

  // Menu phải: user + logout (nếu đã đăng nhập)
  const rightMenuItems = isAuthenticated
    ? [
        {
          key: 'user',
          icon: <UserOutlined />,
          label: user?.name || user?.email || 'User',
        },
        {
          key: 'logout',
          icon: <LogoutOutlined />,
          label: 'Đăng xuất',
          onClick: logout,
        },
      ]
    : [
        {
          key: 'login',
          label: 'Đăng nhập',
          onClick: () => window.location.href = '/login',
        },
      ];

  return (
    <Layout>
      {/* Header: logo + menu trái + menu phải */}
      <Header style={{ display: 'flex', alignItems: 'center', background: '#001529' }}>
        <div style={{ color: 'white', fontSize: 20, fontWeight: 'bold', marginRight: 50 }}>
          PlagiarismGuard 2.0
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[current]}
          items={menuItems}
          style={{ flex: 1, minWidth: 0 }}
        />
        <Menu
          theme="dark"
          mode="horizontal"
          items={rightMenuItems}
          style={{ minWidth: 200 }}
        />
      </Header>

      {/* Nội dung chính bọc trong ErrorBoundary */}
      <ErrorBoundary>
        {children}
      </ErrorBoundary>

      {/* Footer: thông tin copyright */}
      <Footer style={{ textAlign: 'center', background: '#f5f5f5' }}>
        PlagiarismGuard ©{new Date().getFullYear()} - MinHash + LSH Plagiarism Detection
      </Footer>
    </Layout>
  );
};

/**
 * Component gốc của ứng dụng (App)
 * - Bọc toàn bộ trong ConfigProvider để áp dụng theme
 * - Sử dụng AppLayout làm layout chung
 * - Định nghĩa routes với public (login) và protected (các trang khác)
 */
function App() {
  return (
    <ConfigProvider theme={themeConfig}>
      <AppLayout>
        <Routes>
          {/* Route public: không cần đăng nhập */}
          <Route path="/login" element={<LoginPage />} />

          {/* Route protected: yêu cầu đăng nhập */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <HomePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/upload"
            element={
              <ProtectedRoute>
                <UploadPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/result/:jobId"
            element={
              <ProtectedRoute>
                <ResultPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <HistoryPage />
              </ProtectedRoute>
            }
          />

          {/* Fallback: redirect về trang chủ nếu route không tồn tại */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </ConfigProvider>
  );
}

export default App;