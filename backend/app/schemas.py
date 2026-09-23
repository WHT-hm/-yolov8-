"""Pydantic 数据模型定义"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BoundingBox(BaseModel):
    """检测框坐标（相对图片宽高的归一化比例 0~1）"""
    pest_name: str
    confidence: float
    x: float
    y: float
    width: float
    height: float


class DetectionRecord(BaseModel):
    id: int
    image_url: str
    thumbnail_url: str
    crop_type: str
    pest_types: List[str]
    severity: str  # 低 / 中 / 高
    avg_confidence: float
    boxes: List[BoundingBox]
    created_at: datetime
    remark: Optional[str] = None


class DetectionListResponse(BaseModel):
    items: List[DetectionRecord]
    total: int
    page: int
    page_size: int


class SeverityCount(BaseModel):
    level: str
    count: int


class SpeciesCount(BaseModel):
    name: str
    count: int


class TrendPoint(BaseModel):
    date: str
    count: int


class DashboardStats(BaseModel):
    total_detections: int
    today_detections: int
    pest_species_count: int
    avg_confidence: float
    severity_distribution: List[SeverityCount]
    species_distribution: List[SpeciesCount]
    trend: List[TrendPoint]


class MetaOptions(BaseModel):
    pest_types: List[str]
    crop_types: List[str]
    severity_levels: List[str]


# ------------------ 用户认证 ------------------

class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ------------------ 用户设置 ------------------

class UserSettingsUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    model_name: Optional[str] = None
    theme: Optional[str] = None


class UserSettingsOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    api_base_url: Optional[str] = None
    model_name: Optional[str] = None
    theme: str
    has_api_key: bool
    api_key_masked: Optional[str] = None


class ConnectionTestRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    api_key: Optional[str] = None
    api_base_url: str
    model_name: Optional[str] = None


class ConnectionTestResult(BaseModel):
    success: bool
    status_code: Optional[int] = None
    message: str
