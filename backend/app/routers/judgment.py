"""判断模型（Jev）相关路由。

`judgment_model.judge_yolo_result`（复核 YOLO 识别结果，见 README"判断模型
接入设计"一节）现在由 `POST /api/detections` 在每次检测后自动调用一次。
本路由提供的 `/verify` 是**手动重新触发**入口，用于给判断模型配置之前创建
的旧记录补一次复核，或者单纯想再拿一次新的复核意见——不是唯一的触发方式。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, judgment_model, mock_data, models
from ..database import get_db
from ..schemas import JudgmentStatusOut, YoloVerificationOut

router = APIRouter(prefix="/api/judgment", tags=["judgment"])


@router.get("/status", response_model=JudgmentStatusOut)
def get_judgment_status(
    current_user: models.User = Depends(auth.get_current_user),
):
    """供前端判断是否要展示"AI 复核"入口：是否已在设置页配置判断模型接口。"""
    settings = current_user.settings
    configured = bool(settings and settings.api_base_url)
    return JudgmentStatusOut(configured=configured)


@router.post("/detections/{detection_id}/verify", response_model=YoloVerificationOut)
async def verify_detection(
    detection_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """对指定检测记录的识别结果发起一次判断模型复核，并把结论写入该记录的 remark。"""
    detection = db.query(models.Detection).filter(models.Detection.id == detection_id).first()
    if not detection:
        raise HTTPException(status_code=404, detail="记录不存在")

    # 权限检查：与 detections.py 中其它按记录操作的接口保持一致
    if current_user.role != "super_admin" and detection.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="无权限访问该记录")

    record = detection.to_dict()
    pest_types = record["pest_types"]
    if not pest_types:
        raise HTTPException(status_code=400, detail="该记录没有识别出任何病虫害，无需复核")

    result = await judgment_model.judge_yolo_result(
        settings=current_user.settings,
        predicted_pest=pest_types[0],
        predicted_confidence=record["avg_confidence"],
        crop_type=record["crop_type"],
        pest_crop_map=mock_data.PEST_CROP_MAP,
    )
    if result is None:
        raise HTTPException(status_code=503, detail="判断模型未配置或调用失败，无法完成复核")

    detection.remark = result.note
    db.commit()

    return YoloVerificationOut(
        detection_id=detection_id,
        is_plausible=result.is_plausible,
        confidence_alignment=result.confidence_alignment,
        suggested_alternative=result.suggested_alternative,
        note=result.note,
    )
