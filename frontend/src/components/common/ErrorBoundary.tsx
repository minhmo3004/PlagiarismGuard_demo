import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button } from 'antd';

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
    errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = {
            hasError: false,
            error: null,
            errorInfo: null,
        };
    }

    static getDerivedStateFromError(error: Error): Partial<State> {
        return { hasError: true };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('ErrorBoundary caught an error:', error, errorInfo);
        this.setState({
            error,
            errorInfo,
        });
    }

    handleReset = () => {
        this.setState({
            hasError: false,
            error: null,
            errorInfo: null,
        });
        window.location.reload();
    };

    render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <div style={{ padding: '50px', textAlign: 'center' }}>
                    <Result
                        status="error"
                        title="Đã xảy ra lỗi"
                        subTitle="Xin lỗi, có lỗi không mong muốn xảy ra. Vui lòng thử lại."
                        extra={[
                            <Button type="primary" key="reload" onClick={this.handleReset}>
                                Tải lại trang
                            </Button>,
                            <Button key="home" onClick={() => window.location.href = '/'}>
                                Về trang chủ
                            </Button>,
                        ]}
                    >
                        {process.env.NODE_ENV === 'development' && this.state.error && (
                            <div style={{ textAlign: 'left', marginTop: 20 }}>
                                <details style={{ whiteSpace: 'pre-wrap' }}>
                                    <summary>Chi tiết lỗi (Development mode)</summary>
                                    <p>{this.state.error.toString()}</p>
                                    <p>{this.state.errorInfo?.componentStack}</p>
                                </details>
                            </div>
                        )}
                    </Result>
                </div>
            );
        }

        return this.props.children;
    }
}
