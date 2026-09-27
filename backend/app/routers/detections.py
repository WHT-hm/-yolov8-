import json
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from .. import auth, mock_data, models
from ..database import get_db
from ..schemas import DetectionListResponse, DetectionRecord

router = APIRouter(prefix="/api/detections", tags=["detections"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@router.get("", response_model=DetectionListResponse)
def list_detections(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    pest_type: Optional[str] = None,
    severity: Optional[str] = None,
    keyword: Optional[str] = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """列出检测记录，超级管理员看全部，普通管理员只看自己机构的"""
    query = db.query(models.Detection)

    # 权限过滤：非超级管理员只能看自己机构的记录
    if current_user.role != "super_admin":
        query = query.filter(models.Detection.org_id == current_user.org_id)

    # 功能过滤
    if pest_type:
        # pest_types 存储为 JSON 字符串，需要查询时处理
        # SQLite 的 JSON 查询比较复杂，这里用 Python 过滤
        pass  # 在后处理中过滤
    if severity:
        query = query.filter(models.Detection.severity == severity)
    if keyword:
        query = query.filter(
            (models.Detection.crop_type.ilike(f"%{keyword}%")) |
            (models.Detection.pest_types.ilike(f"%{keyword}%"))
        )

    total = query.count()
    detections = query.order_by(models.Detection.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # 转换为 DetectionRecord
    items = []
    for det in detections:
        record_dict = det.to_dict()
        # 事后过滤 pest_type
        if pest_type and pest_type not in record_dict["pest_types"]:
            continue
        items.append(DetectionRecord(**record_dict))

    return DetectionListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{detection_id}", response_model=DetectionRecord)
def get_detection(
    detection_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """获取单条检测记录"""
    detection = db.query(models.Detection).filter(models.Detection.id == detection_id).first()
    if not detection:
        raise HTTPException(status_code=404, detail="记录不存在")

    # 权限检查
    if current_user.role != "super_admin" and detection.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="无权限访问该记录")

    return DetectionRecord(**detection.to_dict())


@router.post("", response_model=DetectionRecord)
async def create_detection(
    file: UploadFile = File(...),
    crop_type: Optional[str] = Form(None),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """接收上传图片，返回模拟检测结果，并保存到数据库"""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="仅支持图片文件 (jpg/png/bmp/webp)")

    filename = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    image_url = f"/static/uploads/{filename}"

    # 生成模拟检测结果
    mock_result = mock_data.create_mock_detection(crop_type, image_url)

    # 保存到数据库
    detection = models.Detection(
        user_id=current_user.id,
        org_id=current_user.org_id,
        image_url=image_url,
        thumbnail_url=image_url,
        crop_type=mock_result.crop_type,
        pest_types=json.dumps(mock_result.pest_types),
        severity=mock_result.severity,
        avg_confidence=int(round(mock_result.avg_confidence * 100)),  # Store as 0-100 percentage
        boxes=json.dumps([box.dict() for box in mock_result.boxes]),
    )
    db.add(detection)
    db.commit()
    db.refresh(detection)

    return DetectionRecord(**detection.to_dict())


@router.delete("/{detection_id}")
def delete_detection(
    detection_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """删除检测记录"""
    detection = db.query(models.Detection).filter(models.Detection.id == detection_id).first()
    if not detection:
        raise HTTPException(status_code=404, detail="记录不存在")

    # 权限检查：超级管理员或记录所有者可以删除
    if current_user.role != "super_admin" and detection.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="无权限删除该记录")

    db.delete(detection)
    db.commit()
    return {"success": True}

