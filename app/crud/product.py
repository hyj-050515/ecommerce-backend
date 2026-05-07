# app/crud/product.py
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.sql import Select
from app.crud.base import CRUDBase
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductSearchParams


class CRUDProduct(CRUDBase[Product]):
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Product]:
        """根据名称获取商品"""
        result = await db.execute(
            select(Product).where(Product.name == name)
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: ProductCreate) -> Product:
        """创建商品"""
        db_obj = Product(
            name=obj_in.name,
            description=obj_in.description,
            price=obj_in.price,
            stock=obj_in.stock,
            image_url=obj_in.image_url,
            category=obj_in.category,
            is_active=obj_in.is_active,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get_multi_with_filter(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        size: int = 20,
        search_params: Optional[ProductSearchParams] = None
    ) -> Tuple[list[Product], int]:
        """
        分页获取商品列表（支持搜索和筛选）
        
        返回：(商品列表, 总数量)
        """
        # 构建基础查询
        query = select(Product)
        
        # 应用筛选条件
        if search_params:
            # 关键词搜索（名称或描述）
            if search_params.keyword:
                keyword_pattern = f"%{search_params.keyword}%"
                query = query.where(
                    or_(
                        Product.name.like(keyword_pattern),
                        Product.description.like(keyword_pattern)
                    )
                )
            
            # 分类筛选
            if search_params.category:
                query = query.where(Product.category == search_params.category)
            
            # 价格范围
            if search_params.min_price is not None:
                query = query.where(Product.price >= search_params.min_price)
            if search_params.max_price is not None:
                query = query.where(Product.price <= search_params.max_price)
            
            # 上架状态
            if search_params.is_active is not None:
                query = query.where(Product.is_active == search_params.is_active)
            
            # 排序
            if search_params.sort_by:
                sort_field = getattr(Product, search_params.sort_by, None)
                if sort_field:
                    if search_params.sort_order == "asc":
                        query = query.order_by(sort_field.asc())
                    else:
                        query = query.order_by(sort_field.desc())
        
        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 分页
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)
        
        # 执行查询
        result = await db.execute(query)
        items = list(result.scalars().all())
        
        return items, total
    
    async def get_categories(self, db: AsyncSession) -> list[str]:
        """获取所有商品分类"""
        result = await db.execute(
            select(Product.category)
            .where(Product.category.isnot(None))
            .distinct()
        )
        return [row for row in result.scalars().all() if row]
    
    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: Product, 
        obj_in: ProductUpdate
    ) -> Product:
        """更新商品"""
        update_data = obj_in.model_dump(exclude_unset=True)
        return await super().update(db, db_obj=db_obj, obj_in=update_data)


    async def get_active_products(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> list[Product]:
        """获取上架商品列表（前台使用）"""
        result = await db.execute(
            select(Product)
            .where(Product.is_active == True)
            .where(Product.stock > 0)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def check_stock(
        self, 
        db: AsyncSession, 
        *, 
        product_id: int, 
        quantity: int
    ) -> Tuple[bool, Optional[Product]]:
        """
        检查商品库存是否足够
        
        返回：(是否足够, 商品对象)
        """
        product = await self.get(db, id=product_id)
        if not product:
            return False, None
        if not product.is_active:
            return False, product
        if product.stock < quantity:
            return False, product
        return True, product

    async def reduce_stock(
        self,
        db: AsyncSession,
        *,
        product_id: int,
        quantity: int
    ) -> Optional[Product]:
        """
        减少商品库存（下单时使用）
        
        注意：调用前应先使用 check_stock 验证
        """
        product = await self.get(db, id=product_id)
        if product:
            product.stock -= quantity
            await db.commit()
            await db.refresh(product)
        return product

    async def increase_stock(
        self,
        db: AsyncSession,
        *,
        product_id: int,
        quantity: int
    ) -> Optional[Product]:
        """
        增加商品库存（取消订单/退货时使用）
        """
        product = await self.get(db, id=product_id)
        if product:
            product.stock += quantity
            await db.commit()
            await db.refresh(product)
        return product

# 单例实例
product = CRUDProduct(Product)