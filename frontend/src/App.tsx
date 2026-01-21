import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, Layout, Menu } from 'antd';
import {
    HomeOutlined,
    UploadOutlined,
    HistoryOutlined,
    UserOutlined,
    LogoutOutlined
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

// Theme configuration
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

// Protected Route Component
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

// Main App Layout
const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { isAuthenticated, user, logout } = useAuth();
    const location = window.location.pathname;
    const current = location === '/' ? 'home' : location.substring(1);

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
                icon: <UserOutlined />,
                label: 'Đăng nhập',
                onClick: () => window.location.href = '/login',
            },
        ];

    return (
        <Layout style={{ minHeight: '100vh' }}>
            {isAuthenticated && (
                <Header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
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
            )}

            <ErrorBoundary>
                {children}
            </ErrorBoundary>

            <Footer style={{ textAlign: 'center', background: '#f5f5f5' }}>
                PlagiarismGuard  ©{new Date().getFullYear()} - MinHash + LSH Plagiarism Detection
            </Footer>
        </Layout>
    );
};

function App() {
    return (
        <ConfigProvider theme={themeConfig}>
            <AppLayout>
                <Routes>
                    {/* Public Routes */}
                    <Route path="/login" element={<LoginPage />} />

                    {/* Protected Routes */}
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

                    {/* Fallback */}
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </AppLayout>
        </ConfigProvider>
    );
}

export default App;
