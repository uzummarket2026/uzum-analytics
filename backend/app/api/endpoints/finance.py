from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api import deps
from app.db.models import Expense, Order, User
from app.worker.tasks import sync_expenses_task
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/expenses")
def get_expenses(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Joriy foydalanuvchining xarajatlari."""
    return db.query(Expense).filter(Expense.user_id == current_user.id).all()


@router.get("/stats")
def get_finance_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Joriy foydalanuvchi uchun moliyaviy statistikani hisoblash."""
    uid = current_user.id

    total_revenue = db.query(func.sum(Order.total_price)).filter(Order.user_id == uid).scalar() or 0
    total_expenses = db.query(func.sum(Expense.amount)).filter(Expense.user_id == uid).scalar() or 0
    net_profit = total_revenue - total_expenses

    today = datetime.now()
    daily_stats = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")

        day_revenue = db.query(func.sum(Order.total_price)).filter(
            Order.user_id == uid,
            func.date(Order.created_at) == day_str,
        ).scalar() or 0

        daily_stats.append({
            "name": day.strftime("%a"),
            "revenue": day_revenue,
        })

    return {
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "daily_stats": daily_stats,
    }


@router.post("/expenses/sync")
def sync_expenses(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_user),
):
    """Joriy foydalanuvchining xarajatlarini sinxronlash."""
    background_tasks.add_task(sync_expenses_task, current_user.id)
    return {"message": "Xarajatlarni sinxronlash orqa fonda boshlandi"}
