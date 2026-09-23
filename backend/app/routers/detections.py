import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from .. import mock_data
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
):
    items, total = mock_data.list_detections(page, page_size, pest_type, severity, keyword)
    return DetectionListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{detection_id}", response_model=DetectionRecord)
def get_detection(detection_id: int):
    record = mock_data.get_detection(detection_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


@router.post("", response_model=DetectionRecord)
async def create_detection(file: UploadFile = File(...), crop_type: Optional[str] = Form(None)):
    """接收上传图片，返回模拟检测结果（后续接入 YOLOv8 后替换此处推理逻辑）"""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="仅支持图片文件 (jpg/png/bmp/webp)")

    filename = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    image_url = f"/static/uploads/{filename}"
    record = mock_data.create_mock_detection(crop_type, image_url)
    return record


@router.delete("/{detection_id}")
def delete_detection(detection_id: int):
    ok = mock_data.delete_detection(detection_id)
    if not ok:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"success": True}
