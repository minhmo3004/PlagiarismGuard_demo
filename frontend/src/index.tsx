import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import App from './App';

const root = ReactDOM.createRoot(
    document.getElementById('root') as HTMLElement
);

root.render(
    <React.StrictMode>
        <BrowserRouter
            future={{
                v7_startTransition: true,
                v7_relativeSplatPath: true,
            }}
        >
            <ConfigProvider
                theme={{
                    token: {
                        colorPrimary: '#1890ff',
                    },
                }}
            >
                <App />
            </ConfigProvider>
        </BrowserRouter>
    </React.StrictMode>
);
