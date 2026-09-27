"""Pydantic 数据模型定义"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator


class BoundingBox(BaseModel):
    """检测框坐标（相对图片宽高的归一化比例 0~1）"""
    pest_name: str
    confidence: float
    x: float
    y: float
    width: float
    height: float
    damage_ratio: float  # 该检测框对应区域的受害面积占比（0~100，模拟数据）
    plant_part: str  # 受害部位：叶片 / 茎秆 / 根部 / 其他（模拟数据）


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

    @field_validator('avg_confidence', mode='before')
    @classmethod
    def normalize_confidence(cls, v):
        """确保 avg_confidence 始终是 0-1 的范围（而不是 0-100 的百分比）"""
        if isinstance(v, (int, float)):
            # 如果值大于 1，假设它是百分比整数，自动转换
            if v > 1:
                return v / 100.0
            return float(v)
        return v


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


class PestDamageStat(BaseModel):
    pest_name: str
    avg_damage_ratio: float
    detection_count: int


class PlantPartStat(BaseModel):
    part: str
    count: int
    percentage: float


class DashboardStats(BaseModel):
    total_detections: int
    today_detections: int
    pest_species_count: int
    avg_confidence: float
    severity_distribution: List[SeverityCount]
    species_distribution: List[SpeciesCount]
    trend: List[TrendPoint]
    damage_ranking: List[PestDamageStat]
    part_distribution: List[PlantPartStat]

    @field_validator('avg_confidence', mode='before')
    @classmethod
    def normalize_dashboard_confidence(cls, v):
        """确保 avg_confidence 始终是 0-1 的范围"""
        if isinstance(v, (int, float)):
            if v > 1:
                return v / 100.0
            return float(v)
        return v


class RiskAlert(BaseModel):
    level: str  # 低 / 中 / 高
    pest_name: Optional[str] = None
    crop_type: Optional[str] = None
    message: str
    basis: str
    generated_at: datetime


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
    role: str = "admin"  # super_admin / admin
    org_id: Optional[int] = None
    org_name: Optional[str] = None
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


# ------------------ 组织/机构管理 ------------------

class OrganizationCreate(BaseModel):
    """创建机构时同时创建管理员账号"""
    name: str  # 机构名称
    admin_username: str
    admin_email: str
    admin_password: str


class OrganizationOut(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class OrganizationDetail(BaseModel):
    """机构详情，包含统计信息"""
    id: int
    name: str
    total_detections: int
    recent_detection_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ------------------ 检测记录数据库版本 ------------------

class DetectionRecordDB(BaseModel):
    """从数据库读取的检测记录（序列化格式）"""
    id: int
    image_url: str
    thumbnail_url: str
    crop_type: str
    pest_types: List[str]
    severity: str
    avg_confidence: float
    boxes: List[BoundingBox]
    created_at: datetime
    remark: Optional[str] = None

    class Config:
        from_attributes = True

    @field_validator('avg_confidence', mode='before')
    @classmethod
    def normalize_db_confidence(cls, v):
        """确保 avg_confidence 始终是 0-1 的范围"""
        if isinstance(v, (int, float)):
            if v > 1:
                return v / 100.0
            return float(v)
        return v

