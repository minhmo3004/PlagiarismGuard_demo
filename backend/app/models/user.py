"""
Pydantic models for database tables
"""
from pydantic import BaseModel, EmailStr, UUID4
from datetime import datetime
from typing import Optional
from enum import Enum


class UserTier(str, Enum):
    """User subscription tiers"""
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"


class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    tier: UserTier = UserTier.FREE


class UserCreate(UserBase):
    """User creation model"""
    password: str


class UserInDB(UserBase):
    """User model in database"""
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
    """User model for API responses"""
    id: UUID4
    daily_uploads: int
    daily_checks: int
    created_at: datetime

    class Config:
        from_attributes = True
