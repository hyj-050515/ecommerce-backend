# app/api/v1/products.py
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud.product import product as product_crud
from app.schemas.product import (
    ProductOut, 
    ProductListResponse, 
    ProductSearchParams
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=ProductListResponse)
async def list_products(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="商品分类"),
    min_price: Optional[float] = Query(None, ge=0, description="最低价格"),
    max_price: Optional[float] = Query(None, ge=0, description="最高价格"),
    sort_by: Optional[str] = Query("created_at", description="排序字段"),
    sort_order: Optional[str] = Query("desc", description="排序方向")
):
    """
    获取商品列表（公开接口）
    - 支持分页、搜索、筛选、排序
    - 默认只返回上架且有库存的商品
    """
    # 构建搜索参数
    search_params = ProductSearchParams(
        keyword=keyword,
        category=category,
        min_price=min_price,
        max_price=max_price,
        is_active=True,  # 前台只显示上架商品
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # 查询商品
    items, total = await product_crud.get_multi_with_filter(
        db,
        page=page,
        size=size,
        search_params=search_params
    )
    
    # 计算总页数
    pages = (total + size - 1) // size if total > 0 else 1
    
    return ProductListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取商品详情（公开接口）
    """
    product = await product_crud.get(db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@router.get("/categories/all", response_model=list[str])
async def get_categories(
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有商品分类（公开接口）
    """
    categories = await product_crud.get_categories(db)
    return categories