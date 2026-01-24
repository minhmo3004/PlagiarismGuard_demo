import React, { useEffect, useState } from 'react';
import { Layout, Typography, Card, Row, Col, Button, Progress, Tag, List, Empty } from 'antd';
import { useNavigate } from 'react-router-dom';
import { CheckCircleOutlined, WarningOutlined, HistoryOutlined, UploadOutlined } from '@ant-design/icons';
import { getPlagiarismResult, PlagiarismCheckResult } from '../services/api';

const { Content } = Layout;
const { Title, Text } = Typography;

/**
 * Trang Kết quả kiểm tra (Result Page)
 * - Hiển thị chi tiết kết quả kiểm tra đạo văn: độ tương đồng, thống kê, danh sách trùng khớp
 * - Lấy dữ liệu từ API hoặc lưu trữ tạm (storedResult)
 * - Hiển thị empty state nếu không có kết quả
 * - Hỗ trợ điều hướng về upload hoặc lịch sử
 */
export const ResultPage: React.FC = () => {
  const navigate = useNavigate();

  // Kết quả kiểm tra đạo văn (null nếu chưa có)
  const [result, setResult] = useState<PlagiarismCheckResult | null>(null);

  // Lấy kết quả từ API khi component mount
  useEffect(() => {
    const storedResult = getPlagiarismResult();
    if (storedResult) {
      setResult(storedResult);
    }
  }, []);

  // Không có kết quả → hiển thị empty state với nút CTA
  if (!result) {
    return (
      <Layout>
        <Content style={{ padding: '50px', maxWidth: 900, margin: '0 auto', textAlign: 'center' }}>
          <Empty
            description="Không có kết quả kiểm tra"
            style={{ marginTop: 100 }}
          >
            <Button type="primary" icon={<UploadOutlined />} onClick={() => navigate('/upload')}>
              Kiểm tra ngay
            </Button>
          </Empty>
        </Content>
      </Layout>
    );
  }

  /**
   * Hàm helper: trả về màu sắc dựa trên mức độ đạo văn
   * - high → đỏ (#ff4d4f)
   * - medium → vàng (#faad14)
   * - low / default → xanh (#52c41a)
   */
  const getColor = () => {
    switch (result.plagiarism_level) {
      case 'high': return '#ff4d4f';
      case 'medium': return '#faad14';
      case 'low': return '#52c41a';
      default: return '#52c41a';
    }
  };

  /**
   * Hàm helper: trả về text mức độ đạo văn
   * - high → CAO
   * - medium → TRUNG BÌNH
   * - low → THẤP
   * - default → KHÔNG PHÁT HIỆN
   */
  const getLevelText = () => {
    switch (result.plagiarism_level) {
      case 'high': return 'CAO';
      case 'medium': return 'TRUNG BÌNH';
      case 'low': return 'THẤP';
      default: return 'KHÔNG PHÁT HIỆN';
    }
  };

  return (
    <Layout>
      <Content style={{ padding: '50px', maxWidth: 900, margin: '0 auto' }}>
        {/* Tiêu đề trang + tên file */}
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <Title level={2}>Kết Quả Kiểm Tra</Title>
          <Text type="secondary">{result.filename}</Text>
        </div>

        <Row gutter={[24, 24]}>
          {/* Card kết quả chính: icon + progress circle + tag mức độ */}
          <Col xs={24} md={12}>
            <Card
              style={{ textAlign: 'center', height: '100%' }}
              bordered={false}
            >
              <div style={{ marginBottom: 20 }}>
                {result.is_plagiarized ? (
                  <WarningOutlined style={{ fontSize: 48, color: getColor() }} />
                ) : (
                  <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
                )}
              </div>

              <Progress
                type="dashboard"
                percent={result.overall_similarity}
                strokeColor={getColor()}
                format={(percent) => (
                  <div>
                    <div style={{ fontSize: 28, fontWeight: 'bold', color: getColor() }}>
                      {percent}%
                    </div>
                    <div style={{ fontSize: 12, color: '#8c8c8c' }}>ĐỘ TƯƠNG ĐỒNG</div>
                  </div>
                )}
                size={180}
              />

              <div style={{ marginTop: 20 }}>
                <Tag
                  color={getColor()}
                  style={{ fontSize: 14, padding: '4px 16px' }}
                >
                  Mức độ: {getLevelText()}
                </Tag>
              </div>
            </Card>
          </Col>

          {/* Card thống kê thông tin */}
          <Col xs={24} md={12}>
            <Card title="Thông tin" style={{ height: '100%' }}>
              <p><strong>Tên file:</strong> {result.filename}</p>
              <p><strong>Số từ:</strong> {result.word_count.toLocaleString()}</p>
              <p><strong>Thời gian xử lý:</strong> {result.processing_time_ms}ms</p>
              <p><strong>Corpus:</strong> {result.corpus_size} tài liệu</p>
              <p><strong>Số nguồn trùng khớp:</strong> {result.matches.length}</p>
            </Card>
          </Col>
        </Row>

        {/* Danh sách tài liệu trùng khớp (nếu có) */}
        {result.matches.length > 0 && (
          <Card title="Danh sách tài liệu trùng khớp" style={{ marginTop: 24 }}>
            <List
              dataSource={result.matches}
              renderItem={(match, index) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={
                      <Tag
                        color={match.similarity >= 70 ? 'red' : match.similarity >= 40 ? 'orange' : 'green'}
                        style={{ width: 60, textAlign: 'center' }}
                      >
                        {match.similarity}%
                      </Tag>
                    }
                    title={match.title}
                    description={
                      <div>
                        <Text type="secondary">
                          {match.author} - {match.university}
                          {match.year && ` (${match.year})`}
                        </Text>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        )}

        {/* Nút hành động: kiểm tra mới hoặc xem lịch sử */}
        <div style={{ marginTop: 40, textAlign: 'center' }}>
          <Button
            type="primary"
            icon={<UploadOutlined />}
            size="large"
            onClick={() => navigate('/upload')}
            style={{ marginRight: 16 }}
          >
            Kiểm tra tài liệu khác
          </Button>
          <Button
            icon={<HistoryOutlined />}
            size="large"
            onClick={() => navigate('/history')}
          >
            Xem lịch sử
          </Button>
        </div>
      </Content>
    </Layout>
  );
};