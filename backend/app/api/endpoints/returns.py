from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.api.deps import get_db
from app.db.models import Return
from app.worker.tasks import sync_returns_task
from app.schemas.return_data import ReturnSchema

router = APIRouter()

@router.get("/", response_model=List[ReturnSchema])
def get_returns(db: Session = Depends(get_db)):
    """Bazadagi qaytarilgan mahsulotlar (Return) nakladnoylarini va ichidagi tovarlarni olish"""
    return db.query(Return).options(joinedload(Return.items)).all()

@router.post("/sync")
def sync_returns(background_tasks: BackgroundTasks):
    """Qaytarishlarni sinxronlashni ishga tushirish"""
    background_tasks.add_task(sync_returns_task)
    return {"message": "Qaytarishlarni sinxronlash orqa fonda boshlandi"}
