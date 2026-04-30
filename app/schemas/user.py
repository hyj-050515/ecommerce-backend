# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
import re

# 共享属性
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str | None = None

# 创建用户时的请求体
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r'[A-Za-z]', v) or not re.search(r'[0-9]', v):
            raise ValueError('Password must contain both letters and numbers')
        return v

# 更新用户（可选字段）
class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=50)
    full_name: str | None = None
    password: str | None = Field(None, min_length=6)

# 返回给客户端的用户信息（不含密码）
class UserOut(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime 

    class Config:
        from_attributes = True  # SQLAlchemy 2.0 使用 from_attributes