"""多机构/子系统管理接口"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth as auth_module, models
from ..database import get_db
from ..schemas import OrganizationCreate, OrganizationDetail, OrganizationOut, DetectionListResponse

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationOut)
def create_organization(
    payload: OrganizationCreate,
    current_user: models.User = Depends(auth_module.require_super_admin),
    db: Session = Depends(get_db),
):
    """创建新的子系统/机构，同时为该机构创建管理员账号"""
    # 检查机构名称是否已存在
    if db.query(models.Organization).filter(models.Organization.name == payload.name).first():
        raise HTTPException(status_code=400, detail="机构名称已存在")

    # 检查管理员用户名和邮箱
    if db.query(models.User).filter(models.User.username == payload.admin_username).first():
        raise HTTPException(status_code=400, detail="管理员用户名已被注册")
    if db.query(models.User).filter(models.User.email == payload.admin_email).first():
        raise HTTPException(status_code=400, detail="管理员邮箱已被注册")

    # 创建机构
    org = models.Organization(name=payload.name)
    db.add(org)
    db.flush()  # 获取自动生成的 org.id

    # 创建管理员账号
    admin_user = models.User(
        username=payload.admin_username,
        email=payload.admin_email,
        hashed_password=auth_module.hash_password(payload.admin_password),
        role="admin",
        org_id=org.id,
    )
    db.add(admin_user)
    db.commit()
    db.refresh(org)

    return OrganizationOut.from_orm(org)


@router.get("", response_model=list[OrganizationDetail])
def list_organizations(
    current_user: models.User = Depends(auth_module.require_super_admin),
    db: Session = Depends(get_db),
):
    """列出所有子系统及其统计信息"""
    orgs = db.query(models.Organization).all()

    result = []
    for org in orgs:
        detection_count = db.query(models.Detection).filter(
            models.Detection.org_id == org.id
        ).count()
        recent = db.query(models.Detection).filter(
            models.Detection.org_id == org.id
        ).order_by(models.Detection.created_at.desc()).first()

        result.append(OrganizationDetail(
            id=org.id,
            name=org.name,
            total_detections=detection_count,
            recent_detection_at=recent.created_at if recent else None,
            created_at=org.created_at,
        ))

    return result


@router.get("/{org_id}/detections", response_model=DetectionListResponse)
def get_organization_detections(
    org_id: int,
    page: int = 1,
    page_size: int = 10,
    current_user: models.User = Depends(auth_module.require_super_admin),
    db: Session = Depends(get_db),
):
    """获取指定子系统的检测历史记录"""
    # 检查机构是否存在
    org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="机构不存在")

    # 查询该机构的所有检测记录
    query = db.query(models.Detection).filter(models.Detection.org_id == org_id)
    total = query.count()

    detections = query.order_by(models.Detection.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # 转换为 DetectionRecord 格式
    from ..schemas import DetectionRecord
    items = [DetectionRecord(**detection.to_dict()) for detection in detections]

    return DetectionListResponse(items=items, total=total, page=page, page_size=page_size)
