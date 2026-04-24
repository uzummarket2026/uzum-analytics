from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api import deps
from app.db.models import Shop, Product, Order
from pydantic import BaseModel

router = APIRouter()

class ShopOut(BaseModel):
    id: int
    uzum_shop_id: Optional[int] = None
    name: str
    is_active: bool
    product_count: Optional[int] = 0
    order_count: Optional[int] = 0

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ShopOut])
def read_shops(db: Session = Depends(deps.get_db)):
    """Barcha faol do'konlarni qaytaradi (mahsulot va buyurtma soni bilan)."""
    shops = db.query(Shop).filter(Shop.is_active == True).all()
    result = []
    for shop in shops:
        product_count = db.query(func.count(Product.id)).filter(Product.shop_id == shop.id).scalar() or 0
        order_count = db.query(func.count(Order.id)).filter(Order.shop_id == shop.id).scalar() or 0
        result.append(ShopOut(
            id=shop.id,
            uzum_shop_id=shop.uzum_shop_id,
            name=shop.name,
            is_active=shop.is_active,
            product_count=product_count,
            order_count=order_count,
        ))
    return result

@router.get("/stats")
def get_shops_stats(db: Session = Depends(deps.get_db)):
    """Har bir do'kon uchun moliyaviy statistika."""
    shops = db.query(Shop).filter(Shop.is_active == True).all()
    stats = []
    for shop in shops:
        orders = db.query(Order).filter(Order.shop_id == shop.id).all()
        revenue = sum(o.total_price or 0 for o in orders)
        profit = sum(o.seller_profit or 0 for o in orders)
        order_count = len(orders)
        product_count = db.query(func.count(Product.id)).filter(Product.shop_id == shop.id).scalar() or 0
        stats.append({
            "shop_id": shop.id,
            "uzum_shop_id": shop.uzum_shop_id,
            "name": shop.name,
            "revenue": revenue,
            "profit": profit,
            "order_count": order_count,
            "product_count": product_count,
        })
    return stats

@router.get("/{shop_id}")
def get_shop(shop_id: int, db: Session = Depends(deps.get_db)):
    """Bitta do'kon ma'lumotini qaytaradi."""
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Do'kon topilmadi")
    return shop

