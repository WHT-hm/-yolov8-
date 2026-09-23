"""ORM 数据模型：用户账号与用户设置（模型接口配置、主题等）"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    settings = relationship(
        "UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    api_key = Column(String(255), nullable=True, default=None)
    api_base_url = Column(String(255), nullable=True, default=None)
    model_name = Column(String(120), nullable=True, default=None)
    theme = Column(String(30), nullable=False, default="forest")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="settings")
