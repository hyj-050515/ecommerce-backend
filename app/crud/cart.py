# app/crud/cart.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload
from app.crud.base import CRUDBase
from app.models.cart import CartItem
from app.schemas.cart import CartItemCreate, CartItemUpdate
from app.crud.product import product as product_crud

class CRUDCart(CRUDBase[CartItem]):
    async def get_user_cart(
        self, db: AsyncSession, *, user_id: int
    ) -> list[CartItem]:
        """获取用户购物车（含商品详情）"""
        result = await db.execute(
            select(CartItem)
            .where(CartItem.user_id == user_id)
            .options(selectinload(CartItem.product))  # 预加载商品信息
            .order_by(CartItem.id)
        )
        return list(result.scalars().all())

    async def get_item(
        self, db: AsyncSession, *, user_id: int, product_id: int
    ) -> Optional[CartItem]:
        """查询用户购物车中某商品"""
        result = await db.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id
            )
        )
        return result.scalar_one_or_none()

    async def add_or_update_item(
        self, db: AsyncSession, *, user_id: int, obj_in: CartItemCreate
    ) -> CartItem:
        """
        添加商品到购物车
        - 如果商品已存在，累加数量
        - 否则创建新记录
        """
        # 检查库存（可选：这里简单验证，实际下单时会再次校验）
        stock_ok, product = await product_crud.check_stock(
            db, product_id=obj_in.product_id, quantity=obj_in.quantity
        )
        if not stock_ok:
            if not product:
                raise ValueError("Product not found")
            elif not product.is_active:
                raise ValueError("Product is not available")
            else:
                raise ValueError(f"Insufficient stock, only {product.stock} left")

        # 查找已有项
        existing = await self.get_item(
            db, user_id=user_id, product_id=obj_in.product_id
        )
        if existing:
            # 更新数量：检查累加后是否超过库存
            new_qty = existing.quantity + obj_in.quantity
            if new_qty > product.stock:
                raise ValueError(
                    f"Cannot add more, maximum available is {product.stock}, "
                    f"you already have {existing.quantity} in cart"
                )
            existing.quantity = new_qty
            await db.commit()
            await db.refresh(existing)
            # 重新加载关联的商品信息
            await db.refresh(existing, attribute_names=["product"])
            return existing
        else:
            # 创建新项
            cart_item = CartItem(
                user_id=user_id,
                product_id=obj_in.product_id,
                quantity=obj_in.quantity
            )
            db.add(cart_item)
            await db.commit()
            await db.refresh(cart_item)
            await db.refresh(cart_item, attribute_names=["product"])
            return cart_item

    async def update_item_quantity(
        self, db: AsyncSession, *, user_id: int, item_id: int, obj_in: CartItemUpdate
    ) -> Optional[CartItem]:
        """
        修改购物车商品数量
        - 数量大于0则更新
        - 数量为0时建议调用删除接口
        """
        result = await db.execute(
            select(CartItem).where(
                CartItem.id == item_id,
                CartItem.user_id == user_id
            )
        )
        cart_item = result.scalar_one_or_none()
        if not cart_item:
            return None

        # 检查库存
        product = await product_crud.get(db, id=cart_item.product_id)
        if product and obj_in.quantity > product.stock:
            raise ValueError(
                f"Insufficient stock, only {product.stock} available"
            )

        cart_item.quantity = obj_in.quantity
        await db.commit()
        await db.refresh(cart_item)
        await db.refresh(cart_item, attribute_names=["product"])
        return cart_item

    async def remove_item(
        self, db: AsyncSession, *, user_id: int, item_id: int
    ) -> bool:
        """删除购物车中的指定商品"""
        result = await db.execute(
            select(CartItem).where(
                CartItem.id == item_id,
                CartItem.user_id == user_id
            )
        )
        item = result.scalar_one_or_none()
        if item:
            await db.delete(item)
            await db.commit()
            return True
        return False

    async def clear_cart(self, db: AsyncSession, *, user_id: int) -> int:
        """清空用户购物车，返回删除的记录数"""
        result = await db.execute(
            delete(CartItem).where(CartItem.user_id == user_id)
        )
        await db.commit()
        return result.rowcount

    async def get_cart_summary(self, db: AsyncSession, *, user_id: int) -> dict:
        """获取购物车汇总信息"""
        result = await db.execute(
            select(
                func.count(CartItem.id).label("total_items"),
                func.sum(CartItem.quantity).label("total_quantity")
            ).where(CartItem.user_id == user_id)
        )
        row = result.one()
        return {
            "total_items": row.total_items or 0,
            "total_quantity": row.total_quantity or 0
        }

# 单例实例
cart = CRUDCart(CartItem)