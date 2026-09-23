"""用户设置接口：模型 API 接入配置（密钥 / 地址 / 模型名）与界面主题"""
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import auth, models
from ..database import get_db
from ..schemas import ConnectionTestRequest, ConnectionTestResult, UserSettingsOut, UserSettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _mask_key(key: str) -> str:
    if len(key) <= 4:
        return "*" * len(key)
    return f"{key[:3]}...{key[-4:]}"


def _get_or_create_settings(db: Session, user: models.User) -> models.UserSettings:
    if user.settings is None:
        settings = models.UserSettings(user_id=user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
        return settings
    return user.settings


def _to_out(settings: models.UserSettings) -> UserSettingsOut:
    has_key = bool(settings.api_key)
    return UserSettingsOut(
        api_base_url=settings.api_base_url,
        model_name=settings.model_name,
        theme=settings.theme,
        has_api_key=has_key,
        api_key_masked=_mask_key(settings.api_key) if has_key else None,
    )


@router.get("", response_model=UserSettingsOut)
def get_settings(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    settings = _get_or_create_settings(db, current_user)
    return _to_out(settings)


@router.put("", response_model=UserSettingsOut)
def update_settings(
    payload: UserSettingsUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    settings = _get_or_create_settings(db, current_user)
    if payload.api_key:
        settings.api_key = payload.api_key
    if payload.api_base_url is not None:
        settings.api_base_url = payload.api_base_url
    if payload.model_name is not None:
        settings.model_name = payload.model_name
    if payload.theme is not None:
        settings.theme = payload.theme
    db.commit()
    db.refresh(settings)
    return _to_out(settings)


@router.post("/test", response_model=ConnectionTestResult)
async def test_connection(
    payload: ConnectionTestRequest,
    current_user: models.User = Depends(auth.get_current_user),
):
    headers = {"Authorization": f"Bearer {payload.api_key}"} if payload.api_key else {}
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.get(payload.api_base_url, headers=headers)
        return ConnectionTestResult(
            success=resp.status_code < 500,
            status_code=resp.status_code,
            message=f"已连接到接口地址，服务器返回状态码 {resp.status_code}",
        )
    except httpx.TimeoutException:
        return ConnectionTestResult(success=False, message="连接超时，请检查接口地址是否正确")
    except httpx.RequestError as exc:
        return ConnectionTestResult(success=False, message=f"连接失败：{exc}")
