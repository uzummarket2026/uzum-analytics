from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.db.models import SystemSetting, User
from pydantic import BaseModel

router = APIRouter()


class SettingUpdate(BaseModel):
    key: str
    value: str


@router.get("/")
def get_settings(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    items = db.query(SystemSetting).filter(SystemSetting.user_id == current_user.id).all()
    return [
        {"key": s.key, "value": "***" if "token" in s.key.lower() else s.value}
        for s in items
    ]


@router.post("/")
def update_setting(
    setting: SettingUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    db_setting = db.query(SystemSetting).filter(
        SystemSetting.user_id == current_user.id,
        SystemSetting.key == setting.key,
    ).first()
    if db_setting:
        db_setting.value = setting.value
    else:
        db_setting = SystemSetting(
            user_id=current_user.id,
            key=setting.key,
            value=setting.value,
        )
        db.add(db_setting)
    db.commit()
    return {"message": f"Setting '{setting.key}' updated successfully"}


@router.get("/token")
def get_token_status(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    token = db.query(SystemSetting).filter(
        SystemSetting.user_id == current_user.id,
        SystemSetting.key == "uzum_api_token",
    ).first()
    return {"has_token": token is not None and len(token.value) > 10}
