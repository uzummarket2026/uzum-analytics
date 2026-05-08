from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.api import deps
from app.db.models import Invoice, User
from app.worker.tasks import sync_invoices_task
from app.schemas.invoice import InvoiceSchema

router = APIRouter()


@router.get("/", response_model=List[InvoiceSchema])
def get_invoices(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Joriy foydalanuvchining yukxatlari (Nakladnoylar) va ichidagi tovarlar."""
    return (
        db.query(Invoice)
        .filter(Invoice.user_id == current_user.id)
        .options(joinedload(Invoice.items))
        .all()
    )


@router.post("/sync")
def sync_invoices(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_user),
):
    """Yukxatlarni joriy foydalanuvchi uchun sinxronlash."""
    background_tasks.add_task(sync_invoices_task, current_user.id)
    return {"message": "Yukxatlarni sinxronlash orqa fonda boshlandi"}
