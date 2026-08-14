from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 1. 优先从环境变量获取连接字符串，并去除可能存在的首尾空格
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.strip()

# 2. 如果没有环境变量，使用本地 127.0.0.1 (比 localhost 更稳定)
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:605678788@127.0.0.1:5000/model_db"

# 3. 彻底修复 UnicodeDecodeError 的关键配置
# connect_args 中的 options 用于强制服务器使用英文消息，避开中文 GBK 错误消息导致的解码失败
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "client_encoding": "utf8",
        "options": "-c lc_messages=C" 
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
