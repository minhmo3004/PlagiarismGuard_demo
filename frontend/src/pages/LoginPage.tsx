import React, { useState } from 'react';
import { Layout, Card, Form, Input, Button, Typography, Tabs } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { useAuth } from '../hooks/useAuth';

const { Content } = Layout;
const { Title } = Typography;

/**
 * Trang Đăng nhập / Đăng ký (Login & Register Page)
 * - Sử dụng Tabs để chuyển đổi giữa hai form: Đăng nhập và Đăng ký
 * - Tích hợp hook useAuth để xử lý login/register
 * - Form validation cơ bản bằng Ant Design Form
 * - Layout căn giữa màn hình, responsive
 */
export const LoginPage: React.FC = () => {
  // Tab đang active: 'login' hoặc 'register'
  const [activeTab, setActiveTab] = useState('login');

  // Lấy các hàm auth từ custom hook
  const { login, register } = useAuth();

  // Instance form để reset fields khi cần
  const [loginForm] = Form.useForm();
  const [registerForm] = Form.useForm();

  /**
   * Xử lý submit form Đăng nhập
   * - Gọi hàm login từ useAuth
   * - Không cần xử lý thêm vì useAuth đã có toast + navigate
   */
  const handleLogin = async (values: { email: string; password: string }) => {
    await login(values.email, values.password);
  };

  /**
   * Xử lý submit form Đăng ký
   * - Gọi hàm register từ useAuth
   * - Nếu thành công: chuyển về tab login + reset form
   */
  const handleRegister = async (values: { email: string; password: string; name: string }) => {
    const success = await register(values.email, values.password, values.name);
    if (success) {
      setActiveTab('login');
      registerForm.resetFields();
    }
  };

  // Cấu hình items cho Tabs (sử dụng API mới của Ant Design để tránh warning TabPane)
  const tabItems = [
    {
      key: 'login',
      label: 'Đăng nhập',
      children: (
        <Form
          form={loginForm}
          name="login"
          onFinish={handleLogin}
          layout="vertical"
          autoComplete="off"
        >
          <Form.Item
            name="email"
            rules={[
              { required: true, message: 'Vui lòng nhập email' },
              { type: 'email', message: 'Email không hợp lệ' },
            ]}
          >
            <Input
              prefix={<MailOutlined />}
              placeholder="Email"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: 'Vui lòng nhập mật khẩu' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Mật khẩu"
              size="large"
            />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" size="large" block>
              Đăng nhập
            </Button>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: 'register',
      label: 'Đăng ký',
      children: (
        <Form
          form={registerForm}
          name="register"
          onFinish={handleRegister}
          layout="vertical"
          autoComplete="off"
        >
          <Form.Item
            name="name"
            rules={[{ required: true, message: 'Vui lòng nhập tên' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="Họ và tên"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="email"
            rules={[
              { required: true, message: 'Vui lòng nhập email' },
              { type: 'email', message: 'Email không hợp lệ' },
            ]}
          >
            <Input
              prefix={<MailOutlined />}
              placeholder="Email"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: 'Vui lòng nhập mật khẩu' },
              { min: 6, message: 'Mật khẩu tối thiểu 6 ký tự' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Mật khẩu"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: 'Vui lòng xác nhận mật khẩu' },
              // Custom validator: kiểm tra mật khẩu khớp nhau
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('Mật khẩu không khớp'));
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Xác nhận mật khẩu"
              size="large"
            />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" size="large" block>
              Đăng ký
            </Button>
          </Form.Item>
        </Form>
      ),
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Content style={{ maxWidth: 450, width: '100%', padding: 20 }}>
        {/* Logo / Tiêu đề ứng dụng */}
        <div style={{ textAlign: 'center', marginBottom: 30 }}>
          <Title level={2}>PlagiarismGuard 2.0</Title>
        </div>

        {/* Card chứa Tabs */}
        <Card>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            centered
            items={tabItems}
          />
        </Card>
      </Content>
    </Layout>
  );
};