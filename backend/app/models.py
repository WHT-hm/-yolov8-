"""ORM 数据模型：用户账号、用户设置、机构、检测记录"""
import json
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Organization(Base):
    """子系统/机构表"""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    detections = relationship("Detection", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="admin")  # super_admin / admin
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)  # 超级管理员为 null
    created_at = Column(DateTime, default=datetime.now)

    settings = relationship(
        "UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    organization = relationship("Organization", back_populates="users")
    detections = relationship("Detection", back_populates="user", cascade="all, delete-orphan")


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


class Detection(Base):
    """检测记录表（将原来内存中的 mock_data._records 持久化）"""
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    image_url = Column(String(255), nullable=False)
    thumbnail_url = Column(String(255), nullable=False)
    crop_type = Column(String(50), nullable=False)
    pest_types = Column(Text, nullable=False)  # JSON 数组字符串，如 '["稻飞虱", "螟虫"]'
    severity = Column(String(10), nullable=False)  # 低 / 中 / 高
    avg_confidence = Column(Integer, nullable=False)  # 百分比，0-100
    boxes = Column(Text, nullable=False)  # JSON 数组字符串，存储完整的检测框信息
    remark = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="detections")
    organization = relationship("Organization", back_populates="detections")

    def to_dict(self):
        """转换为字典格式，用于序列化为 JSON"""
        return {
            "id": self.id,
            "image_url": self.image_url,
            "thumbnail_url": self.thumbnail_url,
            "crop_type": self.crop_type,
            "pest_types": json.loads(self.pest_types) if isinstance(self.pest_types, str) else self.pest_types,
            "severity": self.severity,
            "avg_confidence": self.avg_confidence / 100.0,  # 转换为 0~1 浮点数
            "boxes": json.loads(self.boxes) if isinstance(self.boxes, str) else self.boxes,
            "created_at": self.created_at,
            "remark": self.remark,
        }
