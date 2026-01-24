// index.tsx - Entry point chính của ứng dụng React
// File này chịu trách nhiệm:
// - Tìm element #root trong index.html
// - Render toàn bộ App vào DOM
// - Thiết lập các provider cấp cao nhất (Router, Theme Ant Design, StrictMode)

import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import App from './App';

// Tìm element gốc trong file index.html (thường là <div id="root"></div>)
const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

// Render ứng dụng vào DOM
root.render(
  // StrictMode giúp phát hiện sớm các vấn đề tiềm ẩn trong development
  <React.StrictMode>
    {/* BrowserRouter quản lý routing (các đường dẫn URL) */}
    <BrowserRouter
      // Các option tương lai (future flags) của react-router v7
      // - v7_startTransition: dùng startTransition cho navigation mượt hơn
      // - v7_relativeSplatPath: cải thiện xử lý path wildcard (*)
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      {/* ConfigProvider áp dụng theme Ant Design cho toàn bộ ứng dụng */}
      <ConfigProvider
        theme={{
          token: {
            // Màu chính (primary) dùng cho button, link, các thành phần nổi bật
            colorPrimary: '#1890ff',
            // Có thể mở rộng thêm các token khác ở đây nếu cần đồng bộ với themeConfig.js
          },
        }}
      >
        {/* Component gốc chứa toàn bộ logic và routes của ứng dụng */}
        <App />
      </ConfigProvider>
    </BrowserRouter>
  </React.StrictMode>
);