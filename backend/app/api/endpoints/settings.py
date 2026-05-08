from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.core.crypto import encrypt, decrypt
from app.db.models import SystemSetting, User
from pydantic import BaseModel, Field

router = APIRouter()

SENSITIVE_KEYS = {"uzum_api_token"}


class SettingUpdate(BaseModel):
    key: str = Field(..., min_length=1, max_length=64)
    value: str = Field(..., max_length=4096)


def _is_sensitive(key: str) -> bool:
    k = key.lower()
    return k in SENSITIVE_KEYS or "token" in k or "secret" in k or "password" in k


@router.get("/")
def get_settings(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Sezgir maydonlar (token va b.) hech qachon raw qaytmaydi — faqat ***."""
    items = db.query(SystemSetting).filter(SystemSetting.user_id == current_user.id).all()
    return [
        {"key": s.key, "value": "***" if _is_sensitive(s.key) else s.value}
        for s in items
    ]


@router.post("/")
def update_setting(
    setting: SettingUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Sezgir maydonlar avtomatik shifrlanadi."""
    value_to_store = encrypt(setting.value) if _is_sensitive(setting.key) else setting.value

    db_setting = db.query(SystemSetting).filter(
        SystemSetting.user_id == current_user.id,
        SystemSetting.key == setting.key,
    ).first()
    if db_setting:
        db_setting.value = value_to_store
    else:
        db_setting = SystemSetting(
            user_id=current_user.id,
            key=setting.key,
            value=value_to_store,
        )
        db.add(db_setting)
    db.commit()
    return {"message": f"Setting '{setting.key}' updated successfully"}


@router.get("/token")
def get_token_status(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Token mavjudligini deshifrlangan uzunlikka qarab tekshiradi."""
    token = db.query(SystemSetting).filter(
        SystemSetting.user_id == current_user.id,
        SystemSetting.key == "uzum_api_token",
    ).first()
    if not token or not token.value:
        return {"has_token": False}
    plain = decrypt(token.value) or ""
    return {"has_token": len(plain) > 10}
