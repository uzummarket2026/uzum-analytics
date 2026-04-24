from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ProductBase(BaseModel):
    shop_id: int
    uzum_product_id: int
    sku_id: int
    sku_code: Optional[str] = None
    title: str
    description: Optional[str] = None
    price: float
    purchase_price: Optional[float] = None
    commission_percent: Optional[float] = 0
    stock: int
    fbo_stock: Optional[int] = 0
    fbs_stock: Optional[int] = 0
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ProductSummary(BaseModel):
    total_fbo_value: float
    total_fbo_stock: int
    total_products: int
