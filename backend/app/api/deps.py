"""
Các dependency cho API
Cung cấp các dependency có thể tái sử dụng cho các route
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from app.core.security import decode_token
from app.models.user import User
from typing import Optional

# Scheme xác thực HTTP Bearer token
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Lấy thông tin người dùng hiện tại từ JWT token
    
    Args:
        credentials: Thông tin xác thực Bearer
    
    Returns:
        Đối tượng User
    
    Raises:
        HTTPException: Nếu token không hợp lệ hoặc không tìm thấy người dùng
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "code": "INVALID_TOKEN",
            "message": "Không thể xác thực thông tin đăng nhập"
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # TODO: Lấy thông tin người dùng từ cơ sở dữ liệu
    # user = await get_user_by_id(user_id)
    # if user is None:
    #     raise credentials_exception
    
    # Tạm thời trả về user giả lập (mock)
    # Sau này sẽ thay bằng truy vấn database thực tế
    return User(
        id=user_id,
        email="user@example.com",
        tier="free",
        daily_uploads=0,
        daily_checks=0,
        created_at=None
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Lấy người dùng hiện tại đang hoạt động (có thể thêm kiểm tra bổ sung ở đây)
    
    Args:
        current_user: Người dùng hiện tại từ get_current_user
    
    Returns:
        Đối tượng User nếu đang hoạt động
    """
    # Có thể thêm kiểm tra bổ sung nếu cần (ví dụ: cờ is_active)
    return current_user


async def check_user_quota(user: User) -> bool:
    """
    Kiểm tra xem người dùng còn hạn mức (quota) sử dụng trong ngày hay không
    
    Args:
        user: Đối tượng User
    
    Returns:
        True nếu còn hạn mức, False nếu đã hết
    """
    # TODO: Triển khai kiểm tra quota thực tế từ database
    # Hiện tại chỉ kiểm tra đơn giản dựa trên tier
    
    quota_limits = {
        "free": 10,
        "premium": 100,
        "enterprise": 1000,
        "admin": float('inf')
    }
    
    limit = quota_limits.get(user.tier, 10)
    return user.daily_checks < limit