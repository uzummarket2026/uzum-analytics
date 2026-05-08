from typing import List, Optional
from fastapi import APIRouter, Depends, BackgroundTasks, Response, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api import deps
from app.db.models import Product, User
from app.schemas.product import ProductResponse, ProductSummary
import httpx

router = APIRouter()

@router.get("/summary", response_model=ProductSummary)
def get_product_summary(
    shop_id: Optional[int] = Query(None),
    shop_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """FBO omboridagi mahsulotlar tannarxi va soni haqida ma'lumot."""
    value_query = db.query(func.sum(Product.fbo_stock * func.coalesce(Product.purchase_price, 0))).filter(Product.user_id == current_user.id)
    stock_query = db.query(func.sum(Product.fbo_stock)).filter(Product.user_id == current_user.id)
    count_query = db.query(func.count(Product.id)).filter(Product.user_id == current_user.id)

    if shop_ids:
        value_query = value_query.filter(Product.shop_id.in_(shop_ids))
        stock_query = stock_query.filter(Product.shop_id.in_(shop_ids))
        count_query = count_query.filter(Product.shop_id.in_(shop_ids))
    elif shop_id is not None:
        value_query = value_query.filter(Product.shop_id == shop_id)
        stock_query = stock_query.filter(Product.shop_id == shop_id)
        count_query = count_query.filter(Product.shop_id == shop_id)
    
    total_value = value_query.scalar() or 0
    total_fbo_stock = stock_query.scalar() or 0
    total_products = count_query.scalar() or 0
    
    return {
        "total_fbo_value": total_value,
        "total_fbo_stock": total_fbo_stock,
        "total_products": total_products
    }

@router.get("/", response_model=List[ProductResponse])
def read_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=5000),
    shop_id: Optional[int] = Query(None, description="Bitta do'kon"),
    shop_ids: Optional[List[int]] = Query(None, description="Bir nechta do'kon"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Mahsulotlar ro'yxati. shop_id yoki shop_ids bo'yicha filtrlash."""
    query = db.query(Product).filter(Product.user_id == current_user.id)
    if shop_ids:
        query = query.filter(Product.shop_id.in_(shop_ids))
    elif shop_id is not None:
        query = query.filter(Product.shop_id == shop_id)
    products = query.order_by(Product.id.asc()).offset(skip).limit(limit).all()
    return products

@router.get("/image-proxy")
async def image_proxy(url: str):
    """Uzum rasm serveridan rasmni proxy orqali qaytaradi.

    Auth qo'yilmaydi — chunki <img src> brauzerdan Authorization yubormaydi.
    O'rniga: faqat whitelist hostlarga, redirect'siz, faqat image/* javob.
    """
    from urllib.parse import urlparse

    ALLOWED_HOSTS = {"images.uzum.uz", "static.uzum.uz"}

    parsed = urlparse(url)
    # Faqat absolyut http(s) URL'lar va whitelist'dagi xostlar
    if parsed.scheme not in ("http", "https") or parsed.hostname not in ALLOWED_HOSTS:
        return Response(status_code=400, content="Invalid URL")

    # URL to'liq formatga keltirish (kengaytma yo'q bo'lsa)
    if not any(url.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp")):
        if not url.endswith("/"):
            url += "/"
        url += "t_product_540_high.jpg"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://seller.uzum.uz/",
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    }

    try:
        # follow_redirects=False — SSRF redirect-attack'larni oldini olish
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
            resp = await client.get(url, headers=headers)

            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "image/jpeg")
                if not content_type.startswith("image/"):
                    return Response(status_code=400, content="Not an image")
                return Response(
                    content=resp.content,
                    media_type=content_type,
                    headers={"Cache-Control": "public, max-age=86400"},
                )
            return Response(status_code=resp.status_code)
    except Exception:
        return Response(status_code=502, content="Upstream error")

@router.post("/sync")
def sync_products(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_user),
):
    """Joriy foydalanuvchining do'kon va mahsulotlarini sinxronlash."""
    from app.worker.tasks import sync_uzum_data_task
    background_tasks.add_task(sync_uzum_data_task, current_user.id)
    return {"message": "Shop and Product sync started in background"}


from app.services.uzum_client import UzumClient
from app.worker.tasks import get_api_token


@router.post("/price")
def update_product_price(
    shop_id: int,
    price_data: dict,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Joriy foydalanuvchining do'koni uchun narx yangilash."""
    from app.db.models import Shop
    shop = db.query(Shop).filter(
        Shop.id == shop_id,
        Shop.user_id == current_user.id,
    ).first()
    if not shop:
        return {"error": "Do'kon topilmadi yoki sizniki emas"}

    token = get_api_token(db, current_user.id)
    if not token:
        return {"error": "Uzum API token sozlanmagan"}

    client = UzumClient(api_token=token)
    if client.update_prices(shop.uzum_shop_id, price_data):
        return {"message": "Price updated successfully"}
    return {"error": "Failed to update price"}


@router.post("/stock")
def update_product_stock(
    stock_data: dict,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Joriy foydalanuvchining FBS qoldiqlarini yangilash."""
    token = get_api_token(db, current_user.id)
    if not token:
        return {"error": "Uzum API token sozlanmagan"}

    client = UzumClient(api_token=token)
    if client.update_fbs_stocks(stock_data):
        return {"message": "Stock updated successfully"}
    return {"error": "Failed to update stock"}
