# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 数据库连接字符串
    DATABASE_URL: str = "mysql+aiomysql://ecommerce_user:strong_password@localhost:3306/ecommerce_db"

    # JWT 密钥（生产环境务必修改为复杂随机字符串）
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()