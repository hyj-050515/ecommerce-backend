# app/api/v1/auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app.crud.user import user as user_crud
from app.schemas.user import UserCreate, UserOut
from app.schemas.token import Token
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册
    - 检查邮箱、用户名是否已存在
    - 创建新用户
    """
    # 检查邮箱是否已存在
    existing_email = await user_crud.get_by_email(db, email=user_in.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    # 检查用户名是否已存在
    existing_username = await user_crud.get_by_username(db, username=user_in.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    # 创建用户
    user = await user_crud.create(db, obj_in=user_in)
    return user

@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    用户登录
    - 使用 OAuth2 密码流（username 字段实际为用户名）
    - 返回 JWT access token
    """
    # 验证用户名和密码
    user = await user_crud.authenticate(
        db,
        username=form_data.username,
        password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user_crud.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    # 生成 Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息（需要认证）
    - 在 Swagger 中需要先登录获取 token
    - 点击右上角 Authorize 按钮，输入: Bearer <your_token>
    - 然后调用此接口
    """
    return current_user