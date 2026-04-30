# app/api/v1/__init__.py
from fastapi import APIRouter
from app.api.v1 import auth, products

# 创建主路由
api_router = APIRouter()

# 注册子路由
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(products.router, prefix="/products", tags=["products"])