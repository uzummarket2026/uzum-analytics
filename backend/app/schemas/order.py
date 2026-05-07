from pydantic import BaseModel, model_validator
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
    main_order_id: Optional[int] = None
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
    image_url: Optional[str] = None
    purchase_total: Optional[float] = None      # tannarx × soni
    to_withdraw_amount: Optional[float] = None  # K vivodu = narx − komissiya − logistika
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _fill_image_from_product(cls, data):
        # SQLAlchemy Order obyekti bo'lsa, product.image_url ni image_url ga ko'chiramiz
        if hasattr(data, "product") and getattr(data, "product", None):
            if not getattr(data, "image_url", None):
                try:
                    data.image_url = data.product.image_url
                except Exception:
                    pass
        return data

    class Config:
        from_attributes = True
