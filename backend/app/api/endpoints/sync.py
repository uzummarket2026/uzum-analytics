import time
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.api import deps
from app.db.models import User
from app.worker.tasks import (
    sync_uzum_data_task,
    sync_uzum_orders_task,
    sync_expenses_task,
    sync_invoices_task,
    sync_fbs_orders_task,
    sync_returns_task,
)

router = APIRouter()

# Per-user sync state
_states: dict[int, dict] = {}

SYNC_TIMEOUT_SEC = 30 * 60


def _state_for(user_id: int) -> dict:
    if user_id not in _states:
        _states[user_id] = {
            "running": False,
            "started_at": 0.0,
            "last_result": None,
            "last_error": None,
        }
    return _states[user_id]


def _is_running(user_id: int) -> bool:
    s = _state_for(user_id)
    if s["running"] and (time.time() - s["started_at"]) > SYNC_TIMEOUT_SEC:
        s["running"] = False
        s["last_error"] = "Avtomatik reset (timeout)"
    return s["running"]


def _run_orders_only(user_id: int):
    if _is_running(user_id):
        return
    s = _state_for(user_id)
    s["running"] = True
    s["started_at"] = time.time()
    s["last_error"] = None
    try:
        s["last_result"] = sync_uzum_orders_task(user_id)
    except Exception as e:
        s["last_error"] = str(e)
    finally:
        s["running"] = False


def _run_all(user_id: int):
    if _is_running(user_id):
        return
    s = _state_for(user_id)
    s["running"] = True
    s["started_at"] = time.time()
    s["last_error"] = None
    try:
        print(f"Sync all (user={user_id}): boshlandi")
        sync_uzum_data_task(user_id)
        sync_uzum_orders_task(user_id)
        sync_expenses_task(user_id)
        sync_invoices_task(user_id)
        sync_fbs_orders_task(user_id)
        sync_returns_task(user_id)
        s["last_result"] = "Hammasi sinxronlandi"
        print(f"Sync all (user={user_id}): tugadi")
    except Exception as e:
        s["last_error"] = str(e)
        print(f"Sync all xato: {e}")
    finally:
        s["running"] = False


def auto_sync_all_users():
    """Scheduler chaqiradigan funksiya — har user uchun buyurtma sync."""
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        for u in users:
            try:
                _run_orders_only(u.id)
            except Exception as e:
                print(f"[auto-sync] user={u.id} xato: {e}")
    finally:
        db.close()


@router.post("/all")
def sync_all(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_user),
):
    """Barcha ma'lumotlarni sinxronlash (siz uchun)."""
    if _is_running(current_user.id):
        s = _state_for(current_user.id)
        elapsed = int(time.time() - s["started_at"])
        return {"message": f"Sync ishlamoqda ({elapsed}s)", "status": "running"}
    background_tasks.add_task(_run_all, current_user.id)
    return {"message": "Sinxronizatsiya boshlandi", "status": "started"}


@router.post("/orders")
def sync_orders(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_user),
):
    """Faqat buyurtmalarni sinxronlash (tezroq)."""
    if _is_running(current_user.id):
        s = _state_for(current_user.id)
        elapsed = int(time.time() - s["started_at"])
        return {"message": f"Sync ishlamoqda ({elapsed}s)", "status": "running"}
    background_tasks.add_task(_run_orders_only, current_user.id)
    return {"message": "Buyurtmalar sinxronlash boshlandi", "status": "started"}


@router.get("/status")
def sync_status(current_user: User = Depends(deps.get_current_user)):
    """Hozirgi sync holati va keyingi avtomatik sync vaqti."""
    s = _state_for(current_user.id)
    running = _is_running(current_user.id)

    next_run = None
    try:
        from app.main import scheduler
        job = scheduler.get_job("auto_sync_orders")
        if job and job.next_run_time:
            next_run = job.next_run_time.isoformat()
    except Exception:
        pass

    return {
        "running": running,
        "elapsed_sec": int(time.time() - s["started_at"]) if running else 0,
        "last_result": s["last_result"],
        "last_error": s["last_error"],
        "auto_next_run": next_run,
    }


@router.post("/reset")
def sync_reset(current_user: User = Depends(deps.get_current_user)):
    """Qotib qolgan flag'ni majburan reset qilish."""
    s = _state_for(current_user.id)
    was_running = s["running"]
    s["running"] = False
    s["last_error"] = "Qo'lda reset qilindi" if was_running else None
    return {"message": "Reset OK", "was_running": was_running}
