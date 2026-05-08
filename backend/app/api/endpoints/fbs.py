from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.db.models import FbsOrder, SystemSetting, User
from app.worker.tasks import sync_fbs_orders_task, get_api_token
from app.services.uzum_client import UzumClient

router = APIRouter()


@router.get("/")
def get_fbs_orders(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Joriy foydalanuvchining FBS buyurtmalari."""
    return db.query(FbsOrder).filter(FbsOrder.user_id == current_user.id).all()


@router.post("/sync")
def sync_fbs_orders(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_user),
):
    """FBS buyurtmalarni joriy foydalanuvchi uchun sinxronlash."""
    background_tasks.add_task(sync_fbs_orders_task, current_user.id)
    return {"message": "FBS buyurtmalarni sinxronlash orqa fonda boshlandi"}


@router.post("/{order_id}/confirm")
def confirm_order(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Joriy foydalanuvchining FBS buyurtmasini tasdiqlash."""
    fbs = db.query(FbsOrder).filter(
        FbsOrder.user_id == current_user.id,
        FbsOrder.uzum_order_id == order_id,
    ).first()
    if not fbs:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")

    token = get_api_token(db, current_user.id)
    if not token:
        raise HTTPException(status_code=400, detail="Uzum API token sozlanmagan")

    client = UzumClient(api_token=token)
    if client.confirm_fbs_order(order_id):
        return {"message": "Buyurtma muvaffaqiyatli tasdiqlandi"}
    raise HTTPException(status_code=400, detail="Tasdiqlashda xatolik yuz berdi")


@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    reason: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Joriy foydalanuvchining FBS buyurtmasini bekor qilish."""
    fbs = db.query(FbsOrder).filter(
        FbsOrder.user_id == current_user.id,
        FbsOrder.uzum_order_id == order_id,
    ).first()
    if not fbs:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")

    token = get_api_token(db, current_user.id)
    if not token:
        raise HTTPException(status_code=400, detail="Uzum API token sozlanmagan")

    client = UzumClient(api_token=token)
    if client.cancel_fbs_order(order_id, reason):
        return {"message": "Buyurtma bekor qilindi"}
    raise HTTPException(status_code=400, detail="Bekor qilishda xatolik yuz berdi")
