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

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer credentials
    
    Returns:
        User object
    
    Raises:
        HTTPException: If token is invalid or user not found
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
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # TODO: Get user from database
    # user = await get_user_by_id(user_id)
    # if user is None:
    #     raise credentials_exception
    
    # For now, return mock user
    # This will be replaced with actual database query
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
    Get current active user (can add additional checks here)
    
    Args:
        current_user: Current user from get_current_user
    
    Returns:
        User object if active
    """
    # Add additional checks if needed (e.g., is_active flag)
    return current_user


async def check_user_quota(user: User) -> bool:
    """
    Check if user has remaining quota for today
    
    Args:
        user: User object
    
    Returns:
        True if user has quota remaining
    """
    # TODO: Implement actual quota check from database
    # For now, simple check based on tier
    
    quota_limits = {
        "free": 10,
        "premium": 100,
        "enterprise": 1000,
        "admin": float('inf')
    }
    
    limit = quota_limits.get(user.tier, 10)
    return user.daily_checks < limit
