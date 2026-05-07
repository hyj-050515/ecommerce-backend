# app/api/v1/admin_products.py
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud.product import product as product_crud
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductOut,
    ProductListResponse,
    ProductSearchParams
)
from app.api.deps import get_current_superuser
from app.models.user import User

router = APIRouter(prefix="/admin/products", tags=["admin-products"])


@router.post("/", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    创建商品（仅管理员）
    """
    # 检查商品名称是否已存在
    existing = await product_crud.get_by_name(db, name=product_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with name '{product_in.name}' already exists"
        )
    
    # 创建商品
    product = await product_crud.create(db, obj_in=product_in)
    return product


@router.get("/", response_model=ProductListResponse)
async def list_products_admin(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="商品分类"),
    min_price: Optional[float] = Query(None, ge=0, description="最低价格"),
    max_price: Optional[float] = Query(None, ge=0, description="最高价格"),
    is_active: Optional[bool] = Query(None, description="是否上架"),
    sort_by: Optional[str] = Query("created_at", description="排序字段"),
    sort_order: Optional[str] = Query("desc", description="排序方向")
):
    """
    获取商品列表（管理员）
    - 可查看所有商品（包括下架商品）
    """
    search_params = ProductSearchParams(
        keyword=keyword,
        category=category,
        min_price=min_price,
        max_price=max_price,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    items, total = await product_crud.get_multi_with_filter(
        db,
        page=page,
        size=size,
        search_params=search_params
    )
    
    pages = (total + size - 1) // size if total > 0 else 1
    
    return ProductListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/{product_id}", response_model=ProductOut)
async def get_product_admin(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    获取商品详情（管理员）
    """
    product = await product_crud.get(db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@router.put("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    更新商品信息（仅管理员）
    """
    product = await product_crud.get(db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # 如果更新名称，检查是否重复
    if product_in.name and product_in.name != product.name:
        existing = await product_crud.get_by_name(db, name=product_in.name)
        if existing and existing.id != product_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with name '{product_in.name}' already exists"
            )
    
    product = await product_crud.update(db, db_obj=product, obj_in=product_in)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    删除商品（仅管理员）
    """
    product = await product_crud.get(db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    await product_crud.remove(db, id=product_id)
    return None


@router.patch("/{product_id}/toggle-status", response_model=ProductOut)
async def toggle_product_status(
    product_id: int,
    is_active: bool = Query(..., description="上架状态"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    切换商品上架/下架状态（仅管理员）
    """
    product = await product_crud.get(db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    product.is_active = is_active
    await db.commit()
    await db.refresh(product)
    return product


@router.patch("/{product_id}/stock", response_model=ProductOut)
async def update_product_stock(
    product_id: int,
    stock: int = Query(..., ge=0, description="新库存数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    更新商品库存（仅管理员）
    """
    product = await product_crud.get(db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    product.stock = stock
    await db.commit()
    await db.refresh(product)
    return product