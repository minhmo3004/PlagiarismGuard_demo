import React, { useEffect, useState } from 'react';
import { Layout, Typography, Card, Row, Col, Button, Progress, Tag, List, Empty, Spin } from 'antd';
import { useNavigate, useParams } from 'react-router-dom';
import { CheckCircleOutlined, WarningOutlined, HistoryOutlined, UploadOutlined, SyncOutlined } from '@ant-design/icons';
import { getJobStatus, getCheckResult, PlagiarismCheckResult, getPlagiarismResult } from '../services/api';

const { Content } = Layout;
const { Title, Text } = Typography;

/**
 * Trang Kết quả kiểm tra (Bản PRO - Hỗ trợ Polling)
 */
export const ResultPage: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();

  // State lưu kết quả và trạng thái
  const [result, setResult] = useState<PlagiarismCheckResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string>('pending');

  useEffect(() => {
    let pollInterval: NodeJS.Timeout;

    const fetchResult = async () => {
      // 1. Trường hợp dùng luồng Demo (không có jobId trong URL)
      if (!jobId) {
        const storedResult = getPlagiarismResult();
        if (storedResult) {
          setResult(storedResult);
          setLoading(false);
          setJobStatus('done');
        } else {
          setLoading(false);
        }
        return;
      }

      // 2. Trường hợp dùng luồng Pro (Có jobId) -> Bắt đầu Polling
      setLoading(true);
      
      const poll = async () => {
        try {
          const statusRes = await getJobStatus(jobId);
          setJobStatus(statusRes.status);

          if (statusRes.status === 'done') {
            // Lấy kết quả cuối cùng
            const finalResult = await getCheckResult(jobId);
            setResult(finalResult);
            setLoading(false);
            clearInterval(pollInterval);
          } else if (statusRes.status === 'failed') {
            setError(statusRes.error || 'Quá trình xử lý thất bại');
            setLoading(false);
            clearInterval(pollInterval);
          }
        } catch (err: any) {
          console.error('Polling error:', err);
          setError('Không thể kết nối với server');
          setLoading(false);
          clearInterval(pollInterval);
        }
      };

      // Chạy poll ngay lập tức và sau đó mỗi 3 giây
      poll();
      pollInterval = setInterval(poll, 3000);
    };

    fetchResult();

    // Cleanup interval khi component unmount
    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [jobId]);

  // --- RENDERING LOGIC ---

  // 1. Đang tải hoặc đang xử lý
  if (loading && !result) {
    return (
      <Layout>
        <Content style={{ padding: '50px', textAlign: 'center', marginTop: 100 }}>
          <Card style={{ maxWidth: 600, margin: '0 auto' }}>
            <Spin indicator={<SyncOutlined spin style={{ fontSize: 48 }} />} />
            <div style={{ marginTop: 24 }}>
              <Title level={4}>
                {jobStatus === 'processing' ? 'Đang phân tích tài liệu...' : 'Đang chuẩn bị...'}
              </Title>
              <Text type="secondary">Vui lòng không đóng trình duyệt. Hệ thống đang quét hơn 3,000 tài liệu trong cơ sở dữ liệu.</Text>
            </div>
            <div style={{ marginTop: 24 }}>
               <Tag color="blue">{jobStatus.toUpperCase()}</Tag>
            </div>
          </Card>
        </Content>
      </Layout>
    );
  }

  // 2. Lỗi
  if (error) {
    return (
      <Layout>
        <Content style={{ padding: '50px', textAlign: 'center', marginTop: 100 }}>
          <Card style={{ maxWidth: 600, margin: '0 auto' }}>
            <WarningOutlined style={{ fontSize: 48, color: '#ff4d4f' }} />
            <Title level={4} style={{ marginTop: 24 }}>Lỗi hệ thống</Title>
            <Paragraph>{error}</Paragraph>
            <Button type="primary" onClick={() => navigate('/upload')}>Quay lại Upload</Button>
          </Card>
        </Content>
      </Layout>
    );
  }

  // 3. Không tìm thấy kết quả
  if (!result) {
    return (
      <Layout style={{ minHeight: '100vh', background: '#fff' }}>
        <Content style={{ padding: '50px', maxWidth: 900, margin: '0 auto', textAlign: 'center' }}>
          <Empty description="Không tìm thấy kết quả" style={{ marginTop: 100 }}>
            <Button type="primary" icon={<UploadOutlined />} onClick={() => navigate('/upload')}>Tải lên ngay</Button>
          </Empty>
        </Content>
      </Layout>
    );
  }

  // 4. Hiển thị kết quả (giữ nguyên UI cũ nhưng dùng dữ liệu từ result state)
  const getColor = () => {
    switch (result.plagiarism_level) {
      case 'high': return '#ff4d4f';
      case 'medium': return '#faad14';
      case 'low': return '#52c41a';
      default: return '#52c41a';
    }
  };

  const getLevelText = () => {
    switch (result.plagiarism_level) {
      case 'high': return 'CAO';
      case 'medium': return 'TRUNG BÌNH';
      case 'low': return 'THẤP';
      default: return 'KHÔNG PHÁT HIỆN';
    }
  };

  return (
    <Layout style={{ background: '#fff' }}>
      <Content style={{ padding: '50px', maxWidth: 900, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <Title level={2}>Kết Quả Kiểm Tra</Title>
          <Text type="secondary">{result.filename}</Text>
        </div>

        <Row gutter={[24, 24]}>
          <Col xs={24} md={12}>
            <Card style={{ textAlign: 'center', height: '100%' }} bordered={false}>
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
                    <div style={{ fontSize: 28, fontWeight: 'bold', color: getColor() }}>{percent}%</div>
                    <div style={{ fontSize: 12, color: '#8c8c8c' }}>ĐỘ TƯƠNG ĐỒNG</div>
                  </div>
                )}
                size={180}
              />
              <div style={{ marginTop: 20 }}>
                <Tag color={getColor()} style={{ fontSize: 14, padding: '4px 16px' }}>Mức độ: {getLevelText()}</Tag>
              </div>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card title="Thông số kỹ thuật" style={{ height: '100%' }}>
              <p><strong>Số từ:</strong> {result.word_count.toLocaleString()}</p>
              <p><strong>Thời gian quét:</strong> {result.processing_time_ms}ms</p>
              <p><strong>Nguồn đối chiếu:</strong> Toàn bộ Corpus (PostgreSQL + Redis)</p>
              <p><strong>Số match tìm thấy:</strong> {result.matches.length}</p>
            </Card>
          </Col>
        </Row>

        {result.matches.length > 0 && (
          <Card title="Chi tiết các nguồn trùng khớp" style={{ marginTop: 24 }}>
            <List
              dataSource={result.matches}
              renderItem={(match) => (
                <List.Item style={{ display: 'block' }}>
                  <List.Item.Meta
                    avatar={<Tag color={match.similarity >= 0.7 ? 'red' : 'orange'}>{(match.similarity * 100).toFixed(1)}%</Tag>}
                    title={match.title}
                    description={`${match.author} - ${match.university} ${match.year ? `(${match.year})` : ''}`}
                  />
                  {match.matched_segments && (
                    <div style={{ marginTop: 12, paddingLeft: 40 }}>
                       <details>
                         <summary style={{ color: '#1890ff', cursor: 'pointer' }}>Xem {match.matched_segments.length} đoạn nội dung trùng khớp</summary>
                         <div style={{ marginTop: 12, background: '#f9f9f9', padding: 12, borderRadius: 8 }}>
                           {match.matched_segments.map((seg, i) => (
                             <div key={i} style={{ marginBottom: 12, borderBottom: '1px solid #eee', paddingBottom: 8 }}>
                               <Text type="danger" strong>Bài của bạn: </Text>
                               <Paragraph>"{seg.query_text}"</Paragraph>
                               <Text type="success" strong>Nguồn trùng: </Text>
                               <Paragraph>"{seg.source_text}"</Paragraph>
                             </div>
                           ))}
                         </div>
                       </details>
                    </div>
                  )}
                </List.Item>
              )}
            />
          </Card>
        )}

        <div style={{ marginTop: 40, textAlign: 'center' }}>
          <Button type="primary" icon={<UploadOutlined />} size="large" onClick={() => navigate('/upload')} style={{ marginRight: 16 }}>Kiểm tra bài khác</Button>
          <Button icon={<HistoryOutlined />} size="large" onClick={() => navigate('/history')}>Xem lịch sử</Button>
        </div>
      </Content>
    </Layout>
  );
};

const Paragraph = Typography.Paragraph;