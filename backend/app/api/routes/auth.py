"""
Authentication routes
Register, login, refresh token, logout
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.schemas import UserRegister, UserLogin, Token, TokenRefresh
from app.api.deps import get_current_user
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.models.user import User
from jose import JWTError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Register a new user
    
    - Creates user account
    - Returns access and refresh tokens
    """
    # TODO: Check if email already exists
    # existing_user = await get_user_by_email(user_data.email)
    # if existing_user:
    #     raise HTTPException(400, detail={"code": "EMAIL_EXISTS"})
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # TODO: Create user in database
    # user = await create_user(email=user_data.email, password_hash=hashed_password)
    
    # For now, mock user_id
    user_id = "mock_user_id"
    
    # Create tokens
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Login with email and password
    
    - Validates credentials
    - Returns access and refresh tokens
    """
    # TODO: Get user from database
    # user = await get_user_by_email(credentials.email)
    # if not user or not verify_password(credentials.password, user.password_hash):
    #     raise HTTPException(401, detail={"code": "INVALID_CREDENTIALS"})
    
    # For now, mock validation
    # In production, this should verify against database
    user_id = "mock_user_id"
    
    # Create tokens
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh):
    """
    Refresh access token using refresh token
    
    - Validates refresh token
    - Returns new access and refresh tokens
    """
    try:
        payload = decode_token(token_data.refresh_token)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        
        if user_id is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN"}
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN"}
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    
    - Requires authentication
    - Returns user profile
    """
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user
    
    - Invalidates tokens (if using token blacklist)
    - For stateless JWT, client should discard tokens
    """
    # TODO: Add token to blacklist if implementing token revocation
    # await add_token_to_blacklist(token)
    
    return None
