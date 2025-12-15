import { message, notification } from 'antd';

type ToastType = 'success' | 'error' | 'info' | 'warning';

export const useToast = () => {
    const showToast = (type: ToastType, content: string) => {
        message[type](content);
    };

    const showNotification = (
        type: ToastType,
        title: string,
        description?: string
    ) => {
        notification[type]({
            message: title,
            description,
            placement: 'topRight',
            duration: 4.5,
        });
    };

    return {
        success: (content: string) => showToast('success', content),
        error: (content: string) => showToast('error', content),
        info: (content: string) => showToast('info', content),
        warning: (content: string) => showToast('warning', content),
        showSuccess: (title: string, desc?: string) => showNotification('success', title, desc),
        showError: (title: string, desc?: string) => showNotification('error', title, desc),
        showInfo: (title: string, desc?: string) => showNotification('info', title, desc),
        showWarning: (title: string, desc?: string) => showNotification('warning', title, desc),
    };
};
