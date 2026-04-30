"""
安全模块 - 提供密码加密、验证和 JWT token 生成功能
"""
from datetime import datetime, timedelta, timezone
from app.core.config import settings
import hashlib
import base64
import jwt

def get_password_hash(password: str) -> str:
    """
    生成密码哈希值（使用 PBKDF2 算法）
    
    工作原理：
    1. 从配置中获取 SECRET_KEY 作为盐（salt）
    2. 使用 PBKDF2-HMAC-SHA256 算法对密码进行哈希
    3. 返回 Base64 编码的哈希值
    """
    # 获取盐值（使用 SECRET_KEY 的前 32 字节）
    # 盐的作用：防止彩虹表攻击，相同的密码产生不同的哈希值
    salt = settings.SECRET_KEY.encode('utf-8')[:32]
    
    # 确保盐长度为 32 字节（不够则用 0 填充）
    if len(salt) < 32:
        salt = salt + b'\x00' * (32 - len(salt))
    
    # PBKDF2 哈希算法
    # - sha256: 哈希算法类型
    # - password: 用户密码
    # - salt: 盐值
    # - 100000: 迭代次数（越高越安全，但越慢）
    # - 64: 输出长度（字节）
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',                      # 哈希算法
        password.encode('utf-8'),      # 密码（转字节）
        salt,                          # 盐值
        100000,                        # 迭代次数
        64                             # 输出长度
    )
    
    # Base64 编码：将二进制数据转为可存储的字符串
    return base64.b64encode(hash_bytes).decode('ascii')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否正确
    
    工作原理：
    1. 对输入的明文密码进行相同的哈希计算
    2. 比较计算结果与存储的哈希值是否一致
    """
    # 对明文密码进行哈希，然后与存储的哈希值比较
    return get_password_hash(plain_password) == hashed_password


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    生成 JWT (JSON Web Token) 访问令牌
    
    JWT 结构：
    - Header（头部）：算法类型
    - Payload（负载）：用户数据（如用户名）
    - Signature（签名）：验证 token 真实性
    """
    # 复制数据，避免修改原始字典
    to_encode = data.copy()
    
    # 计算过期时间（UTC 时区）
    if expires_delta:
        # 使用自定义过期时间
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # 使用配置的默认过期时间（通常为 30 分钟）
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # 将过期时间添加到 payload 中
    # 'exp' 是 JWT 标准字段，表示过期时间（expiration）
    to_encode.update({"exp": expire})
    
    # 生成 JWT token
    # - to_encode: 要编码的数据
    # - SECRET_KEY: 签名密钥（必须保密）
    # - algorithm: 签名算法（HS256 = HMAC-SHA256）
    encoded_jwt = jwt.encode(
        to_encode,                      # 负载数据
        settings.SECRET_KEY,            # 签名密钥
        algorithm=settings.ALGORITHM    # 算法（通常为 "HS256"）
    )
    
    return encoded_jwt


# 可选：添加 token 解码函数（用于调试）
def decode_access_token(token: str) -> dict:
    """
    解码 JWT token（用于调试和验证）
    """
    return jwt.decode(
        token, 
        settings.SECRET_KEY, 
        algorithms=[settings.ALGORITHM]
    )