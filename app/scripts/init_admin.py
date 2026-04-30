# app/scripts/init_admin.py
"""
初始化管理员账号脚本
使用方法：python -m app.scripts.init_admin
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.crud.user import user as user_crud
from app.schemas.user import UserCreate


async def create_admin():
    """创建管理员账号"""
    admin_data = UserCreate(
        email="admin@example.com",
        username="admin",
        password="Admin123456",
        full_name="系统管理员"
    )
    
    async with AsyncSessionLocal() as db:
        # 检查是否已存在
        existing = await user_crud.get_by_email(db, email=admin_data.email)
        if existing:
            print(f"⚠️ 管理员账号已存在: {admin_data.email}")
            return
        
        # 检查用户名是否存在
        existing_username = await user_crud.get_by_username(db, username=admin_data.username)
        if existing_username:
            print(f"⚠️ 用户名已存在: {admin_data.username}")
            return
        
        # 创建管理员（直接使用 crud 的 create 方法）
        user = await user_crud.create(db, obj_in=admin_data)
        
        # 设置为超级管理员
        user.is_superuser = True
        await db.commit()
        await db.refresh(user)
        
        print(f"✅ 管理员账号创建成功!")
        print(f"   邮箱: {admin_data.email}")
        print(f"   用户名: {admin_data.username}")
        print(f"   密码: {admin_data.password}")
        print(f"   超级管理员: {user.is_superuser}")


async def main():
    try:
        await create_admin()
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭数据库连接，避免事件循环警告
        from app.core.database import engine
        await engine.dispose()
        print("数据库连接已关闭")


if __name__ == "__main__":
    # Windows 特定的事件循环设置
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())