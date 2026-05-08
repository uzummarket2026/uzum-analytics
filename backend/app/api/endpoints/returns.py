from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.api import deps
from app.db.models import Return, User
from app.worker.tasks import sync_returns_task
from app.schemas.return_data import ReturnSchema

router = APIRouter()


@router.get("/", response_model=List[ReturnSchema])
def get_returns(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Joriy foydalanuvchining qaytarilgan mahsulotlari (Return)."""
    return (
        db.query(Return)
        .filter(Return.user_id == current_user.id)
        .options(joinedload(Return.items))
        .all()
    )


@router.post("/sync")
def sync_returns(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_user),
):
    """Qaytarishlarni joriy foydalanuvchi uchun sinxronlash."""
    background_tasks.add_task(sync_returns_task, current_user.id)
    return {"message": "Qaytarishlarni sinxronlash orqa fonda boshlandi"}
