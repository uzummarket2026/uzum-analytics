from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.deps import get_db
from app.db.models import Expense, Order
from app.worker.tasks import sync_expenses_task
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/expenses")
def get_expenses(db: Session = Depends(get_db)):
    """Bazadagi xarajatlarni olish"""
    return db.query(Expense).all()

@router.get("/stats")
def get_finance_stats(db: Session = Depends(get_db)):
    """Umumiy moliyaviy statistikani hisoblash"""
    # 1. Toplam tushum
    total_revenue = db.query(func.sum(Order.total_price)).scalar() or 0
    
    # 2. Toplam xarajat
    total_expenses = db.query(func.sum(Expense.amount)).scalar() or 0
    
    # 3. Sof foyda
    net_profit = total_revenue - total_expenses
    
    # 4. Kunlik savdo ma'lumotlari (Oxirgi 7 kun)
    today = datetime.now()
    daily_stats = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        
        day_revenue = db.query(func.sum(Order.total_price)).filter(
            func.date(Order.created_at) == day_str
        ).scalar() or 0
        
        daily_stats.append({
            "name": day.strftime("%a"),
            "revenue": day_revenue
        })

    return {
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "daily_stats": daily_stats
    }

@router.post("/expenses/sync")
def sync_expenses(background_tasks: BackgroundTasks):
    """Xarajatlarni sinxronlashni ishga tushirish"""
    background_tasks.add_task(sync_expenses_task)
    return {"message": "Xarajatlarni sinxronlash orqa fonda boshlandi"}
