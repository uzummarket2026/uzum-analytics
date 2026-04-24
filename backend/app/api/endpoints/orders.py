from typing import List, Optional
from fastapi import APIRouter, Depends, BackgroundTasks, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.db.models import Order
from app.schemas.order import OrderResponse

router = APIRouter()

@router.get("/", response_model=List[OrderResponse])
def read_orders(
    skip: int = 0,
    limit: int = 500,
    shop_id: Optional[int] = Query(None, description="Local Shop ID (DB) bo'yicha filtrlash"),
    uzum_shop_id: Optional[int] = Query(None, description="Uzum API shopId bo'yicha filtrlash"),
    status: Optional[str] = Query(None, description="Status bo'yicha filtrlash (TO_WITHDRAW, PROCESSING, CANCELED)"),
    db: Session = Depends(deps.get_db)
):
    """Buyurtmalar ro'yxati. shop_id yoki uzum_shop_id bo'yicha filtrlash mumkin."""
    query = db.query(Order)
    if shop_id is not None:
        query = query.filter(Order.shop_id == shop_id)
    if uzum_shop_id is not None:
        query = query.filter(Order.uzum_shop_id == uzum_shop_id)
    if status is not None:
        query = query.filter(Order.status == status.lower())
    orders = query.order_by(Order.order_date.desc().nullslast()).offset(skip).limit(limit).all()
    return orders

@router.post("/sync")
def sync_orders(background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    from app.worker.tasks import sync_uzum_orders_task
    background_tasks.add_task(sync_uzum_orders_task)
    return {"message": "Order sync started in background"}

