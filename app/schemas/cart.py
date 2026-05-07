# app/schemas/cart.py
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from app.schemas.product import ProductOut  # 复用商品输出 Schema

# ========== 请求体 ==========

class CartItemCreate(BaseModel):
    """添加购物车商品时的请求体"""
    product_id: int = Field(..., gt=0, description="商品ID")
    quantity: int = Field(1, ge=1, description="数量")

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        if v > 999:
            raise ValueError('Quantity cannot exceed 999')
        return v

class CartItemUpdate(BaseModel):
    """修改购物车商品数量时的请求体"""
    quantity: int = Field(..., ge=1, le=999, description="新数量")

# ========== 响应体 ==========

class CartItemOut(BaseModel):
    """单个购物车商品响应"""
    id: int
    product_id: int
    quantity: int
    # 嵌套商品详细信息，方便前端展示
    product: ProductOut

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    """购物车列表响应"""
    items: list[CartItemOut]
    total_items: int           # 商品种类数
    total_quantity: int        # 所有商品总数量
    # 后续可扩展总金额等字段，这里先省略