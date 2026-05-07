# app/api/v1/cart.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud.cart import cart as cart_crud
from app.schemas.cart import (
    CartItemCreate,
    CartItemUpdate,
    CartItemOut,
    CartResponse
)
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(tags=["cart"])


@router.get("/", response_model=CartResponse)
async def get_cart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的购物车列表
    - 包含每个商品的详细信息
    - 需要登录
    """
    items = await cart_crud.get_user_cart(db, user_id=current_user.id)
    
    # 计算汇总
    total_items = len(items)
    total_quantity = sum(item.quantity for item in items)
    
    return CartResponse(
        items=items,
        total_items=total_items,
        total_quantity=total_quantity
    )


@router.post("/items", response_model=CartItemOut, status_code=status.HTTP_201_CREATED)
async def add_cart_item(
    item_in: CartItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    添加商品到购物车
    - 如果商品已在购物车中，则累加数量
    - 会检查商品是否存在及库存是否足够
    """
    try:
        cart_item = await cart_crud.add_or_update_item(
            db, user_id=current_user.id, obj_in=item_in
        )
        return cart_item
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/items/{item_id}", response_model=CartItemOut)
async def update_cart_item(
    item_id: int,
    item_in: CartItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    修改购物车中商品的数量
    - item_id: 购物车记录ID（不是商品ID）
    """
    try:
        cart_item = await cart_crud.update_item_quantity(
            db, user_id=current_user.id, item_id=item_id, obj_in=item_in
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    return cart_item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_cart_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    从购物车中删除指定商品
    """
    removed = await cart_crud.remove_item(
        db, user_id=current_user.id, item_id=item_id
    )
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    return None


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    清空当前用户的购物车
    """
    await cart_crud.clear_cart(db, user_id=current_user.id)
    return None