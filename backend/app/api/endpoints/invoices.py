from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.api.deps import get_db
from app.db.models import Invoice
from app.worker.tasks import sync_invoices_task
from app.schemas.invoice import InvoiceSchema

router = APIRouter()

@router.get("/", response_model=List[InvoiceSchema])
def get_invoices(db: Session = Depends(get_db)):
    """Bazadagi yukxatlarni (Nkladnoy) va tovarlarni olish"""
    return db.query(Invoice).options(joinedload(Invoice.items)).all()

@router.post("/sync")
def sync_invoices(background_tasks: BackgroundTasks):
    """Yukxatlarni sinxronlashni ishga tushirish"""
    background_tasks.add_task(sync_invoices_task)
    return {"message": "Yukxatlarni sinxronlash orqa fonda boshlandi"}
