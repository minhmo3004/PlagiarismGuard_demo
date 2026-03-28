"""
API dependencies
Provides reusable dependencies for routes
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from app.core.security import decode_token
from app.models.user import User
from typing import Optional

from app.db.database import SessionLocal
from app.db import models as db_models
import uuid as uuid_module

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Get current authenticated user from JWT token (Database-backed)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "code": "INVALID_TOKEN",
            "message": "Could not validate credentials"
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user_id_str: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id_str is None or token_type != "access":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    db = SessionLocal()
    try:
        try:
            user_uuid = uuid_module.UUID(user_id_str)
        except ValueError:
            raise credentials_exception
            
        db_user = db.query(db_models.User).filter(db_models.User.id == user_uuid).first()
        if db_user is None:
            raise credentials_exception
        
        # Convert SQLAlchemy model to Pydantic model
        return User.from_orm(db_user)
    finally:
        db.close()


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user
    """
    return current_user


async def check_user_quota(user: User) -> bool:
    """
    Check if user has remaining quota for today (Live DB check)
    """
    # Define limits by tier
    quota_limits = {
        "free": 10,
        "premium": 100,
        "enterprise": 1000,
        "admin": 999999
    }
    
    # In a production environment, we would check if the quota 
    # needs to be reset based on last_reset_date.
    # For now, we trust the daily_checks count in the User object.
    limit = quota_limits.get(user.tier, 5) # Default to 5 if unknown tier
    return user.daily_checks < limit
