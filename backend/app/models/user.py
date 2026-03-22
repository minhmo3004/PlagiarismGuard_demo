"""
Các model Pydantic dùng cho bảng người dùng (User)
Bao gồm: cấp bậc người dùng, model cơ sở, tạo mới, lưu trong DB và phản hồi API
"""
from pydantic import BaseModel, EmailStr, UUID4
from datetime import datetime
from typing import Optional
from enum import Enum


class UserTier(str, Enum):
    """Cấp bậc (tier) của người dùng"""
    FREE = "free"           # Miễn phí - hạn mức thấp
    PREMIUM = "premium"     # Cao cấp - hạn mức cao hơn
    ENTERPRISE = "enterprise"  # Doanh nghiệp - hạn mức rất cao
    ADMIN = "admin"         # Quản trị viên - không giới hạn


class UserBase(BaseModel):
    """Model cơ sở cho thông tin người dùng"""
    email: EmailStr
    tier: UserTier = UserTier.FREE


class UserCreate(UserBase):
    """Model dùng để tạo mới người dùng (đăng ký)"""
    password: str


class UserInDB(UserBase):
    """Model đại diện cho bản ghi người dùng trong cơ sở dữ liệu"""
    id: UUID4
    password_hash: str
    daily_uploads: int = 0
    daily_checks: int = 0
    last_reset_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class User(UserBase):
    """Model dùng cho phản hồi API (response) - không lộ thông tin nhạy cảm"""
    id: UUID4
    daily_uploads: int
    daily_checks: int
    created_at: datetime

    class Config:
        from_attributes = True