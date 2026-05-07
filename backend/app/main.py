import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from app.api.api import api_router
from app.core.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/openapi.json"
)

# Avtomatik sinxronlash uchun scheduler (har soatda buyurtmalar)
scheduler = BackgroundScheduler(timezone="Asia/Tashkent")

origins = [o.strip() for o in settings.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.up\.railway\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
def seed_users_and_assign_data():
    """Birinchi ishga tushirishda 3 ta foydalanuvchi yaratiladi
    va eski ma'lumotlar (agar bo'lsa) birinchi foydalanuvchiga biriktiriladi.
    """
    from app.db.session import SessionLocal
    from app.db.models import User, Shop, Product, Order, Expense, Invoice, FbsOrder, Return, SystemSetting
    from app.core import security
    from sqlalchemy import update

    db = SessionLocal()
    try:
        # 3 ta default foydalanuvchi (birinchi ishga tushirishda yaratiladi)
        DEFAULT_USERS = [
            ("user1@local", "user1pass"),
            ("user2@local", "user2pass"),
            ("user3@local", "user3pass"),
        ]
        first_user_id = None
        for email, password in DEFAULT_USERS:
            existing = db.query(User).filter(User.email == email).first()
            if not existing:
                u = User(
                    email=email,
                    hashed_password=security.get_password_hash(password),
                    is_active=True,
                )
                db.add(u)
                db.commit()
                db.refresh(u)
                print(f"[seed] Yaratildi: {email} / {password}")
                if first_user_id is None:
                    first_user_id = u.id
            else:
                if first_user_id is None:
                    first_user_id = existing.id

        # Eski ma'lumotlar (user_id=NULL) birinchi foydalanuvchiga biriktiriladi
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
def force_migrate_columns():
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
