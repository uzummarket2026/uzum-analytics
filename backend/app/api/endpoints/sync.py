from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.api import deps
from app.worker.tasks import (
    sync_uzum_data_task, 
    sync_uzum_orders_task, 
    sync_expenses_task, 
    sync_invoices_task,
    sync_fbs_orders_task,
    sync_returns_task
)

router = APIRouter()
is_syncing = False

def sync_all_wrapper():
    """Barcha vazifalarni ketma-ket bajarish"""
    global is_syncing
    if is_syncing:
        print("Sinxronizatsiya allaqachon ishlamoqda, yangisi boshlanmadi.")
        return
    
    is_syncing = True
    try:
        print("Barcha ma'lumotlarni sinxronlash boshlandi (Sequential)...")
        sync_uzum_data_task()
        sync_uzum_orders_task()
        sync_expenses_task()
        sync_invoices_task()
        sync_fbs_orders_task()
        sync_returns_task()
        print("Barcha ma'lumotlarni sinxronlash yakunlandi.")
    finally:
        is_syncing = False

@router.post("/all")
def sync_all(background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    """Barcha ma'lumotlarni sinxronizatsiya qilish"""
    if is_syncing:
        return {"message": "Sinxronizatsiya jarayoni allaqachon ketmoqda", "status": "running"}
    
    background_tasks.add_task(sync_all_wrapper)
    return {"message": "Barcha ma'lumotlarni sinxronizatsiya qilish boshlandi"}
