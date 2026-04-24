from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class OrderBase(BaseModel):
    product_id: Optional[int] = None
    quantity: int
    total_price: float
    purchase_price: Optional[float] = None
    status: str = "pending"
    order_date: Optional[datetime] = None
    sku_code: Optional[str] = None
    sku_title: Optional[str] = None
    sku_char_title: Optional[str] = None
    sku_char_value: Optional[str] = None

class OrderCreate(OrderBase):
    pass

class OrderResponse(BaseModel):
    id: int
    uzum_order_id: int
    shop_id: Optional[int] = None
    uzum_shop_id: Optional[int] = None
    product_id: Optional[int] = None
    quantity: int
    total_price: float
    purchase_price: Optional[float] = None
    commission_amount: Optional[float] = None
    logistic_fee: Optional[float] = None
    seller_profit: Optional[float] = None
    status: str
    order_date: Optional[datetime] = None
    sku_code: Optional[str] = None
    sku_title: Optional[str] = None
    sku_char_title: Optional[str] = None
    sku_char_value: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
