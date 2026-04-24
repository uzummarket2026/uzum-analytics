from typing import List, Optional
from fastapi import APIRouter, Depends, BackgroundTasks, Response, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.api import deps
from app.db.models import Product
from app.schemas.product import ProductResponse
import httpx

router = APIRouter()

@router.get("/", response_model=List[ProductResponse])
def read_products(
    skip: int = 0,
    shop_id: Optional[int] = Query(None, description="Do'kon ID bo'yicha filtrlash"),
    db: Session = Depends(deps.get_db)
):
    """Mahsulotlar ro'yxati. shop_id bo'yicha filtrlash mumkin."""
    query = db.query(Product)
    if shop_id is not None:
        query = query.filter(Product.shop_id == shop_id)
    products = query.offset(skip).all()
    return products

@router.get("/image-proxy")
async def image_proxy(url: str):
    """
    Uzum rasm serveridan rasmni proxy orqali qaytaradi.
    Hotlinking blokidan o'tish uchun: so'rov brauzerdan emas, serverdan boradi.
    """
    if not url or "images.uzum.uz" not in url:
        return Response(status_code=400, content="Invalid URL")
    
    # URL to'liq formatga keltirish
    if not url.endswith(".jpg") and not url.endswith(".png") and not url.endswith(".webp"):
        if not url.endswith("/"):
            url += "/"
        url += "t_product_540_high.jpg"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://seller.uzum.uz/",
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers, follow_redirects=True)
            
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "image/jpeg")
                return Response(
                    content=resp.content,
                    media_type=content_type,
                    headers={"Cache-Control": "public, max-age=86400"}
                )
            else:
                return Response(status_code=resp.status_code)
    except Exception as e:
        return Response(status_code=500, content=str(e))

@router.post("/sync")
def sync_products(background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    from app.worker.tasks import sync_uzum_data_task
    background_tasks.add_task(sync_uzum_data_task)
    return {"message": "Shop and Product sync started in background"}

@router.post("/backfill-purchase-price")
def backfill_purchase_price(background_tasks: BackgroundTasks):
    """Invoice API'dan tannarxlarni olib mahsulotlarga yozish (fonda)."""
    from app.worker.tasks import backfill_product_purchase_prices
    background_tasks.add_task(backfill_product_purchase_prices)
    return {"message": "Tannarx sinxronlash fonda boshlandi. Yakunlangach sahifani yangilang."}

from app.services.uzum_client import UzumClient
from app.core.config import settings

@router.post("/price")
def update_product_price(shop_id: int, price_data: dict):
    client = UzumClient(api_token=settings.UZUM_API_TOKEN)
    if client.update_prices(shop_id, price_data):
        return {"message": "Price updated successfully"}
    return {"error": "Failed to update price"}

@router.post("/stock")
def update_product_stock(stock_data: dict):
    client = UzumClient(api_token=settings.UZUM_API_TOKEN)
    if client.update_fbs_stocks(stock_data):
        return {"message": "Stock updated successfully"}
    return {"error": "Failed to update stock"}
