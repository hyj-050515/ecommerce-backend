# app/models/__init__.py
# 确保导入所有模型类
from app.models.user import User

# 列出所有模型，方便 Base.metadata 识别
__all__ = ["User"]