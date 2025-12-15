// src/theme/themeConfig.js
export const themeConfig = {
    token: {
        colorPrimary: '#1890ff',
        colorSuccess: '#52c41a',    // Similarity < 30%
        colorWarning: '#faad14',    // Similarity 30-60%
        colorError: '#ff4d4f',      // Similarity > 60%
        colorBgContainer: '#ffffff',
        colorBgLayout: '#f5f5f5',
        colorText: '#262626',
        colorTextSecondary: '#8c8c8c',
        borderRadius: 8,
    },
};

export const getSimilarityColor = (similarity) => {
    if (similarity < 0.3) return '#52c41a';
    if (similarity < 0.6) return '#faad14';
    return '#ff4d4f';
};

export const getSimilarityLevel = (similarity) => {
    if (similarity < 0.3) return { level: 'low', text: 'Thấp', color: 'success' };
    if (similarity < 0.6) return { level: 'medium', text: 'Trung bình', color: 'warning' };
    return { level: 'high', text: 'Cao', color: 'error' };
};
