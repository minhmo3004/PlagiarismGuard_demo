import React from 'react';
import ReactDiffViewer from 'react-diff-viewer';
import { Empty, Spin } from 'antd';

interface DiffViewerProps {
    queryText: string | null | undefined;
    sourceText: string | null | undefined;
    leftTitle?: string;
    rightTitle?: string;
    isLoading?: boolean;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({
    queryText,
    sourceText,
    leftTitle = "Tài liệu nguồn",
    rightTitle = "Tài liệu của bạn",
    isLoading = false
}) => {
    // ✅ Handle null/undefined
    if (isLoading) {
        return (
            <div className="diff-viewer-loading">
                <Spin size="large" tip="Đang tải nội dung..." />
            </div>
        );
    }

    // ✅ Empty state check
    if (!queryText && !sourceText) {
        return (
            <Empty
                description="Không có nội dung để so sánh"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
        );
    }

    // ✅ Safe defaults
    const safeQueryText = queryText || '';
    const safeSourceText = sourceText || '';

    return (
        <ReactDiffViewer
            oldValue={safeSourceText}
            newValue={safeQueryText}
            splitView={true}
            leftTitle={leftTitle}
            rightTitle={rightTitle}
            useDarkTheme={false}
            showDiffOnly={false}
            styles={{
                variables: {
                    light: {
                        diffViewerBackground: '#fff',
                        addedBackground: '#e6ffed',
                        removedBackground: '#ffeef0',
                        wordAddedBackground: '#acf2bd',
                        wordRemovedBackground: '#fdb8c0',
                    }
                }
            }}
        />
    );
};
