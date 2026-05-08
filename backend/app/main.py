import logging
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.api.api import api_router
from app.api import deps
from app.db.models import User
from app.core.config import settings


def _admin_dep(current_user: User = Depends(deps.get_current_user)) -> User:
    """Faqat admin foydalanuvchilar uchun endpoint dependency."""
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin huquqi talab qilinadi")
    return current_user

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/openapi.json"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Avtomatik sinxronlash uchun scheduler (har soatda buyurtmalar)
scheduler = BackgroundScheduler(timezone="Asia/Tashkent")

origins = [o.strip() for o in settings.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

# CORS: faqat aniq origin'lardan. Eski "*.up.railway.app" regex olib tashlandi —
# istalgan railway saytidan API'ga so'rov yuborilishi xavfli edi.
# Agar railway frontend kerak bo'lsa — uni BACKEND_CORS_ORIGINS env'ga to'liq URL
# bilan qo'shing.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Database Migration
@app.on_event("startup")
def migrate_db():
    from app.db.session import engine
    from app.db.base import Base
    from sqlalchemy import text, inspect
    
    print("Database initialization started...")
    # 1. Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # 2. Add columns safely
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if 'products' in tables:
        existing_columns = [c['name'] for c in inspector.get_columns('products')]
        new_product_cols = {
            "fbo_stock": "INTEGER DEFAULT 0",
            "fbs_stock": "INTEGER DEFAULT 0",
            "commission_percent": "FLOAT DEFAULT 0",
            "image_url": "VARCHAR",
            "description": "VARCHAR",
            "purchase_price": "FLOAT",
            "sku_code": "VARCHAR",
        }
        with engine.connect() as conn:
            for col, col_type in new_product_cols.items():
                if col not in existing_columns:
                    print(f"Adding column products.{col}...")
                    try:
                        conn.execute(text(f"ALTER TABLE products ADD COLUMN {col} {col_type}"))
                        conn.commit()
                    except Exception as e:
                        print(f"Error adding {col}: {e}")
        
    if 'orders' in tables:
        existing_order_columns = [c['name'] for c in inspector.get_columns('orders')]
        new_order_cols = {
            "main_order_id": "BIGINT",
            "commission_amount": "FLOAT DEFAULT 0",
            "logistic_fee": "FLOAT DEFAULT 0",
            "seller_profit": "FLOAT DEFAULT 0",
            "shop_id": "INTEGER",
            "uzum_shop_id": "BIGINT",
            "amount_returns": "INTEGER DEFAULT 0",
            "cancelled": "INTEGER DEFAULT 0",
            "withdrawn_profit": "FLOAT DEFAULT 0",
        }
        with engine.connect() as conn:
            for col, col_type in new_order_cols.items():
                if col not in existing_order_columns:
                    print(f"Adding column orders.{col}...")
                    try:
                        conn.execute(text(f"ALTER TABLE orders ADD COLUMN {col} {col_type}"))
                        conn.commit()
                    except Exception as e:
                        print(f"Error adding {col}: {e}")

    if 'expenses' in tables:
        existing_exp_columns = [c['name'] for c in inspector.get_columns('expenses')]
        new_exp_cols = {
            "uzum_payment_id": "BIGINT",
            "name": "VARCHAR",
            "payment_type": "VARCHAR",
            "status": "VARCHAR",
        }
        with engine.connect() as conn:
            for col, col_type in new_exp_cols.items():
                if col not in existing_exp_columns:
                    print(f"Adding column expenses.{col}...")
                    try:
                        conn.execute(text(f"ALTER TABLE expenses ADD COLUMN {col} {col_type}"))
                        conn.commit()
                    except Exception as e:
                        print(f"Error adding {col}: {e}")
        
    # 2b. users jadvaliga is_admin va created_at qo'shish (multi-user/admin uchun)
    if 'users' in tables:
        existing_user_cols = [c['name'] for c in inspector.get_columns('users')]
        new_user_cols = {
            "is_admin": "BOOLEAN DEFAULT FALSE NOT NULL",
            "created_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
        }
        with engine.connect() as conn:
            for col, col_type in new_user_cols.items():
                if col not in existing_user_cols:
                    print(f"Adding column users.{col}...")
                    try:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_type}"))
                        conn.commit()
                    except Exception as e:
                        print(f"Error adding users.{col}: {e}")

        # Eski bazada hech kim admin emas bo'lsa — id=1 bo'lganni admin qilamiz
        with engine.connect() as conn:
            try:
                row = conn.execute(text("SELECT COUNT(*) FROM users WHERE is_admin = TRUE")).scalar()
                if row == 0:
                    conn.execute(text("UPDATE users SET is_admin = TRUE WHERE id = (SELECT MIN(id) FROM users)"))
                    conn.commit()
                    print("[migrate] Birinchi user is_admin=TRUE qilindi (legacy bazadan ko'chirish)")
            except Exception as e:
                print(f"Legacy admin promotion: {e}")

    # 3. user_id ustunini barcha tegishli jadvallarga qo'shish (multi-user uchun)
    user_id_tables = ["shops", "products", "orders", "expenses",
                      "invoices", "fbs_orders", "returns", "system_settings"]
    with engine.connect() as conn:
        for table in user_id_tables:
            if table not in tables:
                continue
            cols = [c['name'] for c in inspector.get_columns(table)]
            if "user_id" not in cols:
                print(f"Adding column {table}.user_id...")
                try:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER"))
                    conn.commit()
                except Exception as e:
                    print(f"Error adding user_id to {table}: {e}")

    # 4. Eski unique constraint'larni olib tashlash (multi-user uchun bir xil
    # qiymatlar bir necha userda bo'lishi mumkin: api_token, uzum_order_id, ...)
    legacy_unique_constraints = [
        ("system_settings", "system_settings_key_key"),
        ("shops", "shops_uzum_shop_id_key"),
        ("products", "products_sku_id_key"),
        ("orders", "orders_uzum_order_id_key"),
    ]
    legacy_unique_indexes = [
        "ix_system_settings_key",
        "ix_shops_uzum_shop_id",
        "ix_products_sku_id",
        "ix_orders_uzum_order_id",
    ]
    with engine.connect() as conn:
        for table, cons in legacy_unique_constraints:
            try:
                conn.execute(text(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {cons}"))
                conn.commit()
            except Exception as e:
                print(f"Drop constraint {cons}: {e}")
        # Postgres'da unique=True alohida unique index yaratadi — uni ham qayta yaratamiz (unique'siz)
        for idx in legacy_unique_indexes:
            try:
                conn.execute(text(f"DROP INDEX IF EXISTS {idx}"))
                conn.commit()
            except Exception as e:
                print(f"Drop index {idx}: {e}")

    print("Database initialization complete.")


@app.on_event("startup")
def seed_admin_and_assign_data():
    """Birinchi ishga tushirishda admin foydalanuvchi yaratiladi (env'dan).
    Eski ma'lumotlar (user_id=NULL) admin'ga biriktiriladi.

    Admin parolini env orqali bering:
        INITIAL_ADMIN_EMAIL=admin@local
        INITIAL_ADMIN_PASSWORD=<kuchli parol>
    Agar env berilmasa, hech qanday user yaratilmaydi.
    """
    import os
    from app.db.session import SessionLocal
    from app.db.models import User, Shop, Product, Order, Expense, Invoice, FbsOrder, Return, SystemSetting
    from app.core import security
    from sqlalchemy import update

    admin_email = os.environ.get("INITIAL_ADMIN_EMAIL")
    admin_password = os.environ.get("INITIAL_ADMIN_PASSWORD")

    db = SessionLocal()
    try:
        first_user_id = None

        # Bazada hech qanday user yo'q bo'lsa va env berilgan bo'lsa — admin yaratamiz
        any_user = db.query(User).first()
        if not any_user:
            if admin_email and admin_password and len(admin_password) >= 8:
                u = User(
                    email=admin_email,
                    hashed_password=security.get_password_hash(admin_password),
                    is_active=True,
                    is_admin=True,
                )
                db.add(u)
                db.commit()
                db.refresh(u)
                first_user_id = u.id
                print(f"[seed] Admin yaratildi: {admin_email}")
            else:
                print("[seed] Hech qanday user yo'q. INITIAL_ADMIN_EMAIL/PASSWORD env "
                      "(kamida 8 belgili parol) berib qayta ishga tushiring.")
        else:
            # Bazada user bor — birinchi adminni topib, eski ma'lumotlarni biriktiramiz
            admin = db.query(User).filter(User.is_admin == True).order_by(User.id.asc()).first()
            if not admin:
                admin = db.query(User).order_by(User.id.asc()).first()
            if admin:
                first_user_id = admin.id

        # Eski ma'lumotlar (user_id=NULL) birinchi admin/userga biriktiriladi
        if first_user_id is not None:
            for Model in [Shop, Product, Order, Expense, Invoice, FbsOrder, Return, SystemSetting]:
                stmt = update(Model).where(Model.user_id.is_(None)).values(user_id=first_user_id)
                result = db.execute(stmt)
                if result.rowcount:
                    print(f"[seed] {Model.__tablename__}: {result.rowcount} ta yozuv user_id={first_user_id} ga biriktirildi")
            db.commit()
    finally:
        db.close()


@app.on_event("startup")
def start_scheduler():
    """Har soatda buyurtmalarni avtomatik sinxronlash (barcha userlar uchun)."""
    from app.api.endpoints.sync import auto_sync_all_users
    if not scheduler.running:
        scheduler.add_job(
            auto_sync_all_users,
            "cron",
            minute=5,
            id="auto_sync_orders",
            replace_existing=True,
            misfire_grace_time=300,
        )
        scheduler.start()
        logger.info("Scheduler ishga tushdi: barcha userlar uchun auto-sync har soatning 5-daqiqasida")
        print("[scheduler] Auto-sync (multi-user) har soatda 05-daqiqada — yoqilgan")


@app.on_event("shutdown")
def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("[scheduler] To'xtatildi")


app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

@app.post("/admin/migrate-columns")
def force_migrate_columns(current_user=Depends(_admin_dep)):
    from app.db.session import engine
    from sqlalchemy import text, inspect

    inspector = inspect(engine)
    results = {"products": {}, "orders": {}}

    product_cols = {
        "image_url": "VARCHAR",
        "description": "VARCHAR",
        "purchase_price": "FLOAT",
        "sku_code": "VARCHAR",
        "fbo_stock": "INTEGER DEFAULT 0",
        "fbs_stock": "INTEGER DEFAULT 0",
        "commission_percent": "FLOAT DEFAULT 0",
    }
    order_cols = {
        "sku_code": "VARCHAR",
        "sku_title": "VARCHAR",
        "sku_char_title": "VARCHAR",
        "sku_char_value": "VARCHAR",
    }

    with engine.connect() as conn:
        for table, cols in [("products", product_cols), ("orders", order_cols)]:
            existing = [c['name'] for c in inspector.get_columns(table)]
            for col, col_type in cols.items():
                if col not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                    conn.commit()
                    results[table][col] = "added"
                else:
                    results[table][col] = "exists"
    return results
