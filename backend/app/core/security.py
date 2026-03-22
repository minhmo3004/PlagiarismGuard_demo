"""
Module bảo mật
Tạo token JWT, mã hóa mật khẩu, xác thực
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

# Context mã hóa mật khẩu (sử dụng bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Kiểm tra mật khẩu gốc so với mật khẩu đã mã hóa
    
    Args:
        plain_password: Mật khẩu dạng văn bản rõ
        hashed_password: Mật khẩu đã được mã hóa bằng bcrypt
    
    Returns:
        True nếu mật khẩu khớp, False nếu không
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Mã hóa mật khẩu bằng bcrypt
    
    Args:
        password: Mật khẩu dạng văn bản rõ
    
    Returns:
        Chuỗi mật khẩu đã được mã hóa (bcrypt hash)
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Tạo access token JWT
    
    Args:
        data: Dữ liệu payload (thường là {"sub": user_id})
        expires_delta: Thời gian hết hạn của token (mặc định lấy từ settings)
    
    Returns:
        Chuỗi token JWT đã mã hóa
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Tạo refresh token JWT
    
    Args:
        data: Dữ liệu payload (thường là {"sub": user_id})
    
    Returns:
        Chuỗi refresh token JWT đã mã hóa
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Giải mã và xác thực token JWT
    
    Args:
        token: Chuỗi token JWT
    
    Returns:
        Payload đã giải mã (dạng dict)
    
    Raises:
        JWTError: Nếu token không hợp lệ hoặc đã hết hạn
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise