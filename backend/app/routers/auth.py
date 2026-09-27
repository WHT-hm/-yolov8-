"""用户注册 / 登录 / 个人信息相关接口"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, models
from ..database import get_db
from ..schemas import PasswordChange, Token, UserCreate, UserLogin, UserOut, UserUpdate

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_to_dict(user: models.User) -> dict:
    """转换 User 对象为字典，包含 org_name 信息"""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "org_id": user.org_id,
        "org_name": user.organization.name if user.organization else None,
        "created_at": user.created_at,
    }


@router.post("/register", response_model=Token)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="用户名已被注册")
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    user = models.User(
        username=payload.username,
        email=payload.email,
        hashed_password=auth.hash_password(payload.password),
        role="admin",  # 默认为普通管理员
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth.create_access_token(user.id)
    user_dict = _user_to_dict(user)
    return Token(access_token=token, user=UserOut(**user_dict))


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not user or not auth.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = auth.create_access_token(user.id)
    user_dict = _user_to_dict(user)
    return Token(access_token=token, user=UserOut(**user_dict))


@router.get("/me", response_model=UserOut)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    user_dict = _user_to_dict(current_user)
    return UserOut(**user_dict)


@router.put("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    if payload.username and payload.username != current_user.username:
        if db.query(models.User).filter(models.User.username == payload.username).first():
            raise HTTPException(status_code=400, detail="用户名已被注册")
        current_user.username = payload.username
    if payload.email and payload.email != current_user.email:
        if db.query(models.User).filter(models.User.email == payload.email).first():
            raise HTTPException(status_code=400, detail="邮箱已被注册")
        current_user.email = payload.email
    db.commit()
    db.refresh(current_user)
    user_dict = _user_to_dict(current_user)
    return UserOut(**user_dict)


@router.post("/change-password")
def change_password(
    payload: PasswordChange,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    if not auth.verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码不正确")
    current_user.hashed_password = auth.hash_password(payload.new_password)
    db.commit()
    return {"success": True}

