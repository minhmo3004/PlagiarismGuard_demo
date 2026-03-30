"""
Các route liên quan đến xác thực
Đăng ký, đăng nhập, làm mới token, đăng xuất
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
from app.models.user import User as PydanticUser
from app.db.database import SessionLocal
from app.db.models import User as DBUser
from jose import JWTError

router = APIRouter(prefix="/auth", tags=["Xác thực"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Đăng ký người dùng mới
    
    - Tạo tài khoản người dùng
    - Trả về access token và refresh token
    """
    db = SessionLocal()
    try:
        # Kiểm tra email đã tồn tại chưa
        existing_user = db.query(DBUser).filter(DBUser.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "EMAIL_EXISTS", "message": "Email đã được đăng ký"}
            )
        
        # Mã hóa mật khẩu và tạo người dùng mới
        hashed_password = get_password_hash(user_data.password)
        db_user = DBUser(email=user_data.email, password_hash=hashed_password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        user_id = str(db_user.id)
        
        # Tạo token
        access_token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )
    finally:
        db.close()


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Đăng nhập bằng email và mật khẩu
    
    - Kiểm tra thông tin đăng nhập
    - Trả về access token và refresh token
    """
    db = SessionLocal()
    try:
        # Lấy thông tin người dùng từ cơ sở dữ liệu
        db_user = db.query(DBUser).filter(DBUser.email == credentials.email).first()
        if not db_user or not verify_password(credentials.password, db_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_CREDENTIALS", "message": "Email hoặc mật khẩu không đúng"}
            )
        
        user_id = str(db_user.id)
        
        # Tạo token
        access_token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )
    finally:
        db.close()


@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh):
    """
    Làm mới access token bằng refresh token
    
    - Kiểm tra tính hợp lệ của refresh token
    - Trả về cặp access token và refresh token mới
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
    
    # Tạo token mới
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.get("/me", response_model=PydanticUser)
async def get_me(current_user: PydanticUser = Depends(get_current_user)):
    """
    Lấy thông tin người dùng hiện tại
    
    - Yêu cầu đã xác thực
    - Trả về thông tin hồ sơ người dùng
    """
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: PydanticUser = Depends(get_current_user)):
    """
    Đăng xuất người dùng hiện tại
    
    - Vô hiệu hóa token (nếu dùng blacklist)
    - Với JWT stateless, client chỉ cần xóa token ở phía client
    """
    # TODO: Thêm token vào blacklist nếu triển khai thu hồi token
    # await add_token_to_blacklist(token)
    
    return None