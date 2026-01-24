import React, { useState, useEffect } from 'react';
import { Layout, Typography, Table, Button, Tag, Space, Popconfirm } from 'antd';
import { EyeOutlined, DeleteOutlined, DownloadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { getComparisonHistory, deleteComparison, downloadHistoryFile, type HistoryItem } from '../services/api';
import { EmptyState } from '../components/common/EmptyState';
import { useToast } from '../hooks/useToast';

const { Content } = Layout;
const { Title } = Typography;

/**
 * Trang Lịch sử kiểm tra (History Page)
 * - Hiển thị danh sách các lần kiểm tra đạo văn trước đây dưới dạng bảng
 * - Hỗ trợ phân trang, xem chi tiết, tải file kết quả, xóa bản ghi
 * - Sử dụng Ant Design Table + EmptyState khi không có dữ liệu
 */
export const HistoryPage: React.FC = () => {
  // Danh sách lịch sử kiểm tra
  const [history, setHistory] = useState<HistoryItem[]>([]);
  // Trạng thái đang tải dữ liệu
  const [loading, setLoading] = useState(true);
  // Tổng số bản ghi (dùng cho phân trang)
  const [total, setTotal] = useState(0);
  // Trang hiện tại
  const [currentPage, setCurrentPage] = useState(1);
  // Số bản ghi mỗi trang (cố định)
  const [pageSize] = useState(10);

  const navigate = useNavigate();
  const { success, error } = useToast();

  // Tải dữ liệu lịch sử khi component mount hoặc currentPage thay đổi
  useEffect(() => {
    loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage]);

  /**
   * Tải danh sách lịch sử kiểm tra từ API
   * - Cập nhật state history và total
   * - Xử lý lỗi và hiển thị toast nếu thất bại
   */
  const loadHistory = async () => {
    setLoading(true);
    try {
      const response = await getComparisonHistory(currentPage, pageSize);
      setHistory(response.items);
      setTotal(response.total);
    } catch (err) {
      error('Không thể tải lịch sử');
      console.error('Failed to load history:', err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Xử lý xóa một bản ghi lịch sử
   * - Gọi API deleteComparison
   * - Tải lại danh sách nếu thành công
   */
  const handleDelete = async (id: string) => {
    try {
      await deleteComparison(id);
      success('Đã xóa');
      loadHistory();
    } catch (err) {
      error('Không thể xóa');
    }
  };

  /**
   * Xử lý tải file kết quả kiểm tra
   * - Gọi API downloadHistoryFile
   * - Thông báo thành công hoặc lỗi (bao gồm trường hợp file không tồn tại)
   */
  const handleDownload = async (id: string, filename: string) => {
    try {
      await downloadHistoryFile(id, filename);
      success('Đang tải file...');
    } catch (err: any) {
      if (err.response?.status === 404) {
        error('File không còn tồn tại');
      } else {
        error('Không thể tải file');
      }
    }
  };

  /**
   * Hàm helper: trả về Tag màu tương ứng với mức độ tương đồng
   * - < 30%   → xanh (Thấp)
   * - < 60%   → vàng (Trung bình)
   * - ≥ 60%   → đỏ (Cao)
   */
  const getSimilarityTag = (similarity: number) => {
    if (similarity < 0.3) {
      return <Tag color="success">Thấp ({Math.round(similarity * 100)}%)</Tag>;
    }
    if (similarity < 0.6) {
      return <Tag color="warning">Trung bình ({Math.round(similarity * 100)}%)</Tag>;
    }
    return <Tag color="error">Cao ({Math.round(similarity * 100)}%)</Tag>;
  };

  // Cấu hình cột cho Table
  const columns = [
    {
      title: 'Tên tài liệu',
      dataIndex: 'query_name',
      key: 'query_name',
      ellipsis: true, // Cắt ngắn nếu tên quá dài
    },
    {
      title: 'Độ tương đồng',
      dataIndex: 'overall_similarity',
      key: 'overall_similarity',
      render: (similarity: number) => getSimilarityTag(similarity),
      sorter: (a: HistoryItem, b: HistoryItem) => a.overall_similarity - b.overall_similarity,
    },
    {
      title: 'Số trùng khớp',
      dataIndex: 'matches_count',
      key: 'matches_count',
      sorter: (a: HistoryItem, b: HistoryItem) => a.matches_count - b.matches_count,
    },
    {
      title: 'Ngày kiểm tra',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString('vi-VN'),
      sorter: (a: HistoryItem, b: HistoryItem) =>
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: 'Thao tác',
      key: 'actions',
      render: (_: any, record: HistoryItem) => (
        <Space>
          {/* Xem chi tiết kết quả */}
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/result/${record.id}`)}
          >
            Xem
          </Button>

          {/* Tải file kết quả */}
          <Button
            type="link"
            icon={<DownloadOutlined />}
            onClick={() => handleDownload(record.id, record.query_name)}
          >
            Tải
          </Button>

          {/* Xác nhận xóa */}
          <Popconfirm
            title="Xác nhận xóa?"
            description="Bạn có chắc muốn xóa kết quả này?"
            onConfirm={() => handleDelete(record.id)}
            okText="Xóa"
            cancelText="Hủy"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
            >
              Xóa
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Không có dữ liệu và không đang tải → hiển thị empty state
  if (!loading && history.length === 0) {
    return (
      <Layout>
        <Content style={{ padding: '50px' }}>
          <EmptyState type="no-history" onAction={() => navigate('/upload')} />
        </Content>
      </Layout>
    );
  }

  return (
    <Layout>
      <Content style={{ padding: '50px' }}>
        {/* Header: tiêu đề + nút kiểm tra mới */}
        <div style={{ marginBottom: 30, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={2}>Lịch sử kiểm tra</Title>
          <Button type="primary" onClick={() => navigate('/upload')}>
            Kiểm tra mới
          </Button>
        </div>

        {/* Bảng lịch sử */}
        <Table
          columns={columns}
          dataSource={history}
          rowKey="id"
          loading={loading}
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: total,
            onChange: (page) => setCurrentPage(page),
            showSizeChanger: false, // Không cho thay đổi số lượng mỗi trang
            showTotal: (total) => `Tổng ${total} kết quả`,
          }}
        />
      </Content>
    </Layout>
  );
};