import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from './useToast';

interface User {
    id: string;
    email: string;
    name: string;
}

interface AuthState {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
}

export const useAuth = () => {
    const [authState, setAuthState] = useState<AuthState>({
        user: null,
        isAuthenticated: false,
        isLoading: true,
    });

    const navigate = useNavigate();
    const { showSuccess, showError } = useToast();

    // Check authentication status on mount
    useEffect(() => {
        const checkAuth = async () => {
            try {
                const token = localStorage.getItem('auth_token');

                if (!token) {
                    setAuthState({ user: null, isAuthenticated: false, isLoading: false });
                    return;
                }

                // TODO: Validate token with backend
                // For now, just check if token exists
                const userStr = localStorage.getItem('user');
                if (userStr) {
                    const user = JSON.parse(userStr);
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

    const login = useCallback(async (email: string, password: string) => {
        try {
            // TODO: Implement actual login API call
            // For now, mock login
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

    const logout = useCallback(() => {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        setAuthState({ user: null, isAuthenticated: false, isLoading: false });
        showSuccess('Đã đăng xuất');
        navigate('/login');
    }, [navigate, showSuccess]);

    const register = useCallback(async (email: string, password: string, name: string) => {
        try {
            // TODO: Implement actual register API call
            showSuccess('Đăng ký thành công', 'Vui lòng đăng nhập');
            navigate('/login');
            return true;
        } catch (error: any) {
            showError('Đăng ký thất bại', error.message);
            return false;
        }
    }, [navigate, showSuccess, showError]);

    return {
        ...authState,
        login,
        logout,
        register,
    };
};
