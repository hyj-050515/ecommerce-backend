# app/schemas/product.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from decimal import Decimal
from typing import Optional

# ==================== 共享属性 ====================
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="商品名称")
    description: Optional[str] = Field(None, max_length=2000, description="商品描述")
    price: float = Field(..., gt=0, description="商品价格")
    stock: int = Field(0, ge=0, description="库存数量")
    image_url: Optional[str] = Field(None, max_length=500, description="商品图片URL")
    category: Optional[str] = Field(None, max_length=100, description="商品分类")
    is_active: bool = Field(True, description="是否上架")

    @field_validator('price')
    @classmethod
    def validate_price(cls, v: float) -> float:
        """验证价格：必须大于0且最多两位小数"""
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        # 检查小数位数
        if round(v, 2) != v:
            raise ValueError('Price can have at most 2 decimal places')
        return v

    @field_validator('stock')
    @classmethod
    def validate_stock(cls, v: int) -> int:
        """验证库存：不能为负数"""
        if v < 0:
            raise ValueError('Stock cannot be negative')
        return v


# ==================== 创建商品 ====================
class ProductCreate(ProductBase):
    """创建商品时的请求体"""
    pass


# ==================== 更新商品 ====================
class ProductUpdate(BaseModel):
    """更新商品（所有字段可选）"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError('Price must be greater than 0')
        if v is not None and round(v, 2) != v:
            raise ValueError('Price can have at most 2 decimal places')
        return v

    @field_validator('stock')
    @classmethod
    def validate_stock(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError('Stock cannot be negative')
        return v


# ==================== 商品响应 ====================
class ProductOut(ProductBase):
    """返回给客户端的商品信息"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # 允许 ORM 对象转换


# ==================== 商品列表响应 ====================
class ProductListResponse(BaseModel):
    """商品列表响应（包含分页信息）"""
    items: list[ProductOut]
    total: int
    page: int
    size: int
    pages: int


# ==================== 商品搜索参数 ====================
class ProductSearchParams(BaseModel):
    """商品搜索参数"""
    keyword: Optional[str] = Field(None, description="搜索关键词（名称/描述）")
    category: Optional[str] = Field(None, description="商品分类")
    min_price: Optional[float] = Field(None, ge=0, description="最低价格")
    max_price: Optional[float] = Field(None, ge=0, description="最高价格")
    is_active: Optional[bool] = Field(None, description="是否上架")
    sort_by: Optional[str] = Field(
        "created_at", 
        description="排序字段：price/stock/created_at"
    )
    sort_order: Optional[str] = Field(
        "desc", 
        description="排序方向：asc/desc"
    )