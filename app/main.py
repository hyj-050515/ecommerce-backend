# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import init_db, close_db,get_db
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动事件
    print("🚀 Application starting up...")
    await init_db()
    print (get_db.__name__)
    yield
    # 关闭事件
    print("👋 Application shutting down...")
    await close_db()


app = FastAPI(
    title="E-commerce API",
    description="简易电商平台后端",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# 配置 CORS（允许前端调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "E-commerce API is running"}