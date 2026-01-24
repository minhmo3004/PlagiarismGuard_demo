import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from './useToast';

// Định nghĩa kiểu dữ liệu cho User
interface User {
  id: string;
  email: string;
  name: string;
}

// Trạng thái authentication tổng thể
interface AuthState {
  user: User | null;          // Thông tin người dùng hiện tại (null nếu chưa đăng nhập)
  isAuthenticated: boolean;   // Đã đăng nhập hay chưa
  isLoading: boolean;         // Đang kiểm tra trạng thái auth (dùng cho loading screen)
}

/**
 * Custom hook quản lý authentication
 * - Kiểm tra token & user khi app khởi động
 * - Cung cấp các hàm: login, logout, register
 * - Lưu trữ token & user vào localStorage (mock hiện tại)
 * - Sử dụng toast để thông báo thành công / lỗi
 * - Tự động điều hướng sau khi login/logout
 */
export const useAuth = () => {
  // Trạng thái auth
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true, // Ban đầu đang kiểm tra
  });

  const navigate = useNavigate();
  const { showSuccess, showError } = useToast();

  // Kiểm tra trạng thái đăng nhập khi component mount (chỉ chạy 1 lần)
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('auth_token');

        // Không có token → chưa đăng nhập
        if (!token) {
          setAuthState({ user: null, isAuthenticated: false, isLoading: false });
          return;
        }

        // TODO: Nên gọi API validate token ở đây (kiểm tra token còn hợp lệ với backend)
        // Hiện tại chỉ kiểm tra token tồn tại + user trong localStorage
        const userStr = localStorage.getItem('user');
        if (userStr) {
          const user = JSON.parse(userStr) as User;
          setAuthState({ user, isAuthenticated: true, isLoading: false });
        } else {
          setAuthState({ user: null, isAuthenticated: false, isLoading: false });
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        setAuthState({ user: null, isAuthenticated: false, isLoading: false });
      }
    };

    checkAuth();
  }, []);

  /**
   * Hàm đăng nhập
   * - Hiện tại dùng mock (lưu token & user vào localStorage)
   * - TODO: Thay bằng gọi API thực tế (POST /login)
   */
  const login = useCallback(async (email: string, password: string) => {
    try {
      // TODO: Thay bằng gọi API login thực tế
      const mockUser: User = {
        id: '1',
        email,
        name: email.split('@')[0],
      };

      const mockToken = 'mock-jwt-token';

      localStorage.setItem('auth_token', mockToken);
      localStorage.setItem('user', JSON.stringify(mockUser));

      setAuthState({ user: mockUser, isAuthenticated: true, isLoading: false });
      showSuccess('Đăng nhập thành công');
      navigate('/');

      return true;
    } catch (error: any) {
      showError('Đăng nhập thất bại', error.message);
      return false;
    }
  }, [navigate, showSuccess, showError]);

  /**
   * Hàm đăng xuất
   * - Xóa token & user khỏi localStorage
   * - Reset trạng thái auth
   * - Điều hướng về trang login
   */
  const logout = useCallback(() => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    setAuthState({ user: null, isAuthenticated: false, isLoading: false });
    showSuccess('Đã đăng xuất');
    navigate('/login');
  }, [navigate, showSuccess]);

  /**
   * Hàm đăng ký tài khoản
   * - Hiện tại chỉ mock (hiển thị thông báo và chuyển về login)
   * - TODO: Thay bằng gọi API register thực tế (POST /register)
   */
  const register = useCallback(async (email: string, password: string, name: string) => {
    try {
      // TODO: Thay bằng gọi API đăng ký thực tế
      showSuccess('Đăng ký thành công', 'Vui lòng đăng nhập');
      navigate('/login');
      return true;
    } catch (error: any) {
      showError('Đăng ký thất bại', error.message);
      return false;
    }
  }, [navigate, showSuccess, showError]);

  // Trả về trạng thái + các hàm thao tác auth
  return {
    ...authState,
    login,
    logout,
    register,
  };
};