from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, BackgroundTasks, Query
from sqlalchemy import or_, cast, String
from sqlalchemy.orm import Session, joinedload
from app.api import deps
from app.db.models import Order, Product, User
from app.schemas.order import OrderResponse

router = APIRouter()


def _apply_filters(query, shop_id, uzum_shop_id, status, search,
                   date_from: Optional[str] = None, date_to: Optional[str] = None,
                   shop_ids: Optional[List[int]] = None,
                   user_id: Optional[int] = None):
    if user_id is not None:
        query = query.filter(Order.user_id == user_id)
    if shop_ids:
        query = query.filter(Order.shop_id.in_(shop_ids))
    elif shop_id is not None:
        query = query.filter(Order.shop_id == shop_id)
    if uzum_shop_id is not None:
        query = query.filter(Order.uzum_shop_id == uzum_shop_id)
    if status is not None:
        query = query.filter(Order.status == status.lower())
    if search:
        like = f"%{search}%"
        query = query.filter(or_(
            cast(Order.uzum_order_id, String).ilike(like),
            cast(Order.main_order_id, String).ilike(like),
            Order.sku_code.ilike(like),
            Order.sku_title.ilike(like),
        ))
    if date_from:
        try:
            dt = datetime.fromisoformat(date_from)
            query = query.filter(Order.order_date >= dt)
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to)
            # Agar faqat sana bo'lsa (vaqt = 00:00), kun oxirigacha kengaytiramiz
            if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
                dt = dt.replace(hour=23, minute=59, second=59)
            query = query.filter(Order.order_date <= dt)
        except ValueError:
            pass
    return query


def _compute_amounts(o, p):
    """Bitta order uchun barcha hisoblangan summalar."""
    qty = o.quantity or 0
    is_cancelled = o.status in ("canceled", "partially_cancelled")

    # Bekor qilingan buyurtmaga hech qanday hisob yo'q
    if is_cancelled:
        return {
            "revenue": 0.0,
            "purchase_total": 0.0,
            "commission": 0.0,
            "logistic": 0.0,
            "to_withdraw": 0.0,
            "profit": 0.0,
        }

    total = float(o.total_price or 0)
    if total == 0 and p and p.price:
        total = float(p.price) * qty

    purchase_unit = o.purchase_price or (p.purchase_price if p else 0) or 0
    purchase_total = float(purchase_unit) * qty

    commission = float(o.commission_amount or 0)
    if commission == 0 and p and p.commission_percent and total > 0:
        commission = total * (float(p.commission_percent) / 100.0)

    logistic = float(o.logistic_fee or 0)
    to_withdraw = total - commission - logistic
    profit = to_withdraw - purchase_total

    return {
        "revenue": total,
        "purchase_total": purchase_total,
        "commission": commission,
        "logistic": logistic,
        "to_withdraw": to_withdraw,
        "profit": profit,
    }


@router.get("/", response_model=List[OrderResponse])
def read_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=5000),
    shop_id: Optional[int] = Query(None),
    shop_ids: Optional[List[int]] = Query(None, description="Bir nechta do'kon bo'yicha"),
    uzum_shop_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="ID, SKU kod yoki nom bo'yicha qidiruv"),
    date_from: Optional[str] = Query(None, description="ISO sana (masalan 2026-05-01)"),
    date_to: Optional[str] = Query(None, description="ISO sana"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Buyurtmalar ro'yxati (pagination + sana filtri)."""
    query = _apply_filters(db.query(Order), shop_id, uzum_shop_id, status, search, date_from, date_to, shop_ids, current_user.id)
    orders = (
        query.options(joinedload(Order.product))
        .order_by(Order.order_date.desc().nullslast())
        .offset(skip).limit(limit).all()
    )

    for o in orders:
        p = o.product
        # Rasm va matn fallback
        if p:
            o.image_url = p.image_url
            if not o.sku_title:
                o.sku_title = p.title
            if not o.sku_code:
                o.sku_code = p.sku_code
        else:
            o.image_url = None

        a = _compute_amounts(o, p)
        o.total_price = a["revenue"]
        o.purchase_total = a["purchase_total"]
        o.commission_amount = a["commission"]
        o.logistic_fee = a["logistic"]
        o.to_withdraw_amount = a["to_withdraw"]
        if not o.seller_profit or o.seller_profit == 0:
            o.seller_profit = a["profit"]

    return orders


@router.get("/count")
def count_orders(
    shop_id: Optional[int] = Query(None),
    shop_ids: Optional[List[int]] = Query(None),
    uzum_shop_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Filtr bo'yicha umumiy buyurtmalar soni."""
    query = _apply_filters(db.query(Order), shop_id, uzum_shop_id, status, search, date_from, date_to, shop_ids, current_user.id)
    return {"count": query.count()}


@router.get("/summary")
def orders_summary(
    shop_id: Optional[int] = Query(None),
    shop_ids: Optional[List[int]] = Query(None),
    uzum_shop_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Buyurtmalar bo'yicha jamlanma (revenue, foyda, komissiya, ...).

    Dashboard'da sana oraligi bilan qo'llaniladi.
    """
    query = _apply_filters(db.query(Order), shop_id, uzum_shop_id, status, None, date_from, date_to, shop_ids, current_user.id)
    orders = query.options(joinedload(Order.product)).all()

    totals = {
        "count": 0,             # to_withdraw + processing (real narxli)
        "count_all": 0,
        "count_cancelled": 0,
        "count_processing": 0,
        "revenue": 0.0,
        "purchase_total": 0.0,
        "commission": 0.0,
        "logistic": 0.0,
        "to_withdraw": 0.0,
        "profit": 0.0,
    }
    for o in orders:
        is_cancelled = o.status in ("canceled", "partially_cancelled")
        totals["count_all"] += 1
        if is_cancelled:
            totals["count_cancelled"] += 1
            continue
        if o.status == "processing":
            totals["count_processing"] += 1

        a = _compute_amounts(o, o.product)
        totals["count"] += 1
        totals["revenue"] += a["revenue"]
        totals["purchase_total"] += a["purchase_total"]
        totals["commission"] += a["commission"]
        totals["logistic"] += a["logistic"]
        totals["to_withdraw"] += a["to_withdraw"]
        totals["profit"] += a["profit"]

    return totals

@router.post("/sync")
def sync_orders(
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    from app.worker.tasks import sync_uzum_orders_task
    background_tasks.add_task(sync_uzum_orders_task, current_user.id)
    return {"message": "Order sync started in background"}

