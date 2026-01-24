import React from 'react';
import { Layout, Typography, Card, Row, Col, Button } from 'antd';
import { FileSearchOutlined, SafetyOutlined, ThunderboltOutlined, CloudOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Content } = Layout;
const { Title, Paragraph } = Typography;

/**
 * Trang chủ (Home Page) của ứng dụng PlagiarismGuard
 * - Giới thiệu ngắn gọn về hệ thống phát hiện đạo văn
 * - Hiển thị các tính năng nổi bật (card grid)
 * - Hướng dẫn 3 bước hoạt động cơ bản
 * - Nút kêu gọi hành động: "Bắt đầu kiểm tra"
 */
export const HomePage: React.FC = () => {
  const navigate = useNavigate();

  // Danh sách các tính năng nổi bật hiển thị dưới dạng card
  const features = [
    {
      icon: <FileSearchOutlined style={{ fontSize: 48, color: '#1890ff' }} />,
      title: 'Phát hiện chính xác',
      description: 'Sử dụng thuật toán MinHash + LSH để phát hiện đạo văn với độ chính xác cao',
    },
    {
      icon: <ThunderboltOutlined style={{ fontSize: 48, color: '#faad14' }} />,
      title: 'Xử lý nhanh',
      description: 'Kiểm tra hàng nghìn tài liệu trong vài giây với công nghệ LSH',
    },
    {
      icon: <SafetyOutlined style={{ fontSize: 48, color: '#52c41a' }} />,
      title: 'An toàn & Bảo mật',
      description: 'Dữ liệu được mã hóa và bảo vệ theo tiêu chuẩn cao nhất',
    },
    {
      icon: <CloudOutlined style={{ fontSize: 48, color: '#722ed1' }} />,
      title: 'Lưu trữ đám mây',
      description: 'Truy cập lịch sử kiểm tra mọi lúc, mọi nơi',
    },
  ];

  return (
    <Layout>
      <Content style={{ padding: '50px' }}>
        {/* Phần hero: tiêu đề chính + mô tả + nút CTA */}
        <div style={{ textAlign: 'center', marginBottom: 50 }}>
          <Title level={1}>PlagiarismGuard</Title>
          <Paragraph style={{ fontSize: 18, color: '#8c8c8c' }}>
            Hệ thống phát hiện đạo văn thông minh với MinHash + LSH
          </Paragraph>
          <Button
            type="primary"
            size="large"
            onClick={() => navigate('/upload')}
            style={{ marginTop: 20 }}
          >
            Bắt đầu kiểm tra
          </Button>
        </div>

        {/* Grid các tính năng nổi bật */}
        <Row gutter={[24, 24]}>
          {features.map((feature, index) => (
            <Col xs={24} sm={12} lg={6} key={index}>
              <Card hoverable style={{ textAlign: 'center', height: '100%' }}>
                <div style={{ marginBottom: 16 }}>{feature.icon}</div>
                <Title level={4}>{feature.title}</Title>
                <Paragraph>{feature.description}</Paragraph>
              </Card>
            </Col>
          ))}
        </Row>

        {/* Phần hướng dẫn cách hoạt động (3 bước) */}
        <Card style={{ marginTop: 50, textAlign: 'center' }}>
          <Title level={3}>Cách hoạt động</Title>
          <Row gutter={[16, 16]} style={{ marginTop: 30 }}>
            <Col xs={24} md={8}>
              <div style={{ padding: 20 }}>
                {/* Bước 1 */}
                <div
                  style={{
                    width: 60,
                    height: 60,
                    borderRadius: '50%',
                    background: '#1890ff',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 24,
                    fontWeight: 'bold',
                    margin: '0 auto 16px',
                  }}
                >
                  1
                </div>
                <Title level={5}>Upload tài liệu</Title>
                <Paragraph>Tải lên file PDF, DOCX, hoặc TXT cần kiểm tra</Paragraph>
              </div>
            </Col>

            <Col xs={24} md={8}>
              <div style={{ padding: 20 }}>
                {/* Bước 2 */}
                <div
                  style={{
                    width: 60,
                    height: 60,
                    borderRadius: '50%',
                    background: '#52c41a',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 24,
                    fontWeight: 'bold',
                    margin: '0 auto 16px',
                  }}
                >
                  2
                </div>
                <Title level={5}>Phân tích</Title>
                <Paragraph>Hệ thống so sánh với hàng nghìn tài liệu trong database</Paragraph>
              </div>
            </Col>

            <Col xs={24} md={8}>
              <div style={{ padding: 20 }}>
                {/* Bước 3 */}
                <div
                  style={{
                    width: 60,
                    height: 60,
                    borderRadius: '50%',
                    background: '#faad14',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 24,
                    fontWeight: 'bold',
                    margin: '0 auto 16px',
                  }}
                >
                  3
                </div>
                <Title level={5}>Xem kết quả</Title>
                <Paragraph>Nhận báo cáo chi tiết với độ tương đồng và đoạn trùng khớp</Paragraph>
               </div>
            </Col>
          </Row>
        </Card>
      </Content>
    </Layout>
  );
};