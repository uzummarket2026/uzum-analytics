from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from app.api import deps
from app.core import security
from app.core.config import settings
from app.db.models import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.post("/register", response_model=UserResponse)
def register(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Yangi foydalanuvchi yaratish — faqat admin."""
    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Faqat admin yangi user yarata oladi")

    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    hashed_password = security.get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login_access_token(
    request: Request,
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            {"sub": str(user.id)}, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


def _is_admin(user: User) -> bool:
    """Admin = users.is_admin=True. Heuristika emas, DB ustuni."""
    return bool(getattr(user, "is_admin", False))


@router.get("/me")
def me(current_user: User = Depends(deps.get_current_user)):
    """Hozirgi foydalanuvchi (is_admin bayrog'i bilan)."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "is_admin": _is_admin(current_user),
    }


@router.get("/users", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Admin — barcha userlarni ko'radi. Boshqalar — faqat o'zini."""
    if _is_admin(current_user):
        return db.query(User).order_by(User.id.asc()).all()
    return [current_user]


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    update: UserUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Admin — har kimni tahrirlay oladi. Boshqalar — faqat o'zini."""
    if not _is_admin(current_user) and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Faqat o'z hisobingizni tahrirlay olasiz")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User topilmadi")

    if update.email and update.email != user.email:
        existing = db.query(User).filter(User.email == update.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Bu login boshqa foydalanuvchida band")
        user.email = update.email
    if update.password:
        user.hashed_password = security.get_password_hash(update.password)
    if update.is_active is not None and _is_admin(current_user):
        user.is_active = update.is_active

    db.commit()
    db.refresh(user)
    return user
