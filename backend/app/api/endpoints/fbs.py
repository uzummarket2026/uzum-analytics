from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.db.models import FbsOrder
from app.worker.tasks import sync_fbs_orders_task
from app.services.uzum_client import UzumClient
from app.core.config import settings

router = APIRouter()

@router.get("/")
def get_fbs_orders(db: Session = Depends(get_db)):
    """Bazadagi FBS buyurtmalarini olish"""
    return db.query(FbsOrder).all()

@router.post("/sync")
def sync_fbs_orders(background_tasks: BackgroundTasks):
    """FBS buyurtmalarni sinxronlashni ishga tushirish"""
    background_tasks.add_task(sync_fbs_orders_task)
    return {"message": "FBS buyurtmalarni sinxronlash orqa fonda boshlandi"}

@router.post("/{order_id}/confirm")
def confirm_order(order_id: int):
    """FBS buyurtmani tasdiqlash"""
    client = UzumClient(api_token=settings.UZUM_API_TOKEN)
    if client.confirm_fbs_order(order_id):
        return {"message": "Buyurtma muvaffaqiyatli tasdiqlandi"}
    raise HTTPException(status_code=400, detail="Tasdiqlashda xatolik yuz berdi")

@router.post("/{order_id}/cancel")
def cancel_order(order_id: int, reason: str):
    """FBS buyurtmani bekor qilish"""
    client = UzumClient(api_token=settings.UZUM_API_TOKEN)
    if client.cancel_fbs_order(order_id, reason):
        return {"message": "Buyurtma bekor qilindi"}
    raise HTTPException(status_code=400, detail="Bekor qilishda xatolik yuz berdi")
