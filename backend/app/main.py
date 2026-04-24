from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/openapi.json"
)

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
        
    print("Database initialization complete.")

app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

@app.post("/admin/migrate-columns")
def force_migrate_columns():
    from app.db.session import engine
    from sqlalchemy import text, inspect

    inspector = inspect(engine)
    results = {}

    product_cols = {
        "image_url": "VARCHAR",
        "description": "VARCHAR",
        "purchase_price": "FLOAT",
        "sku_code": "VARCHAR",
        "fbo_stock": "INTEGER DEFAULT 0",
        "fbs_stock": "INTEGER DEFAULT 0",
        "commission_percent": "FLOAT DEFAULT 0",
    }
    existing = [c['name'] for c in inspector.get_columns('products')]
    with engine.connect() as conn:
        for col, col_type in product_cols.items():
            if col not in existing:
                conn.execute(text(f"ALTER TABLE products ADD COLUMN {col} {col_type}"))
                conn.commit()
                results[col] = "added"
            else:
                results[col] = "exists"
    return results
