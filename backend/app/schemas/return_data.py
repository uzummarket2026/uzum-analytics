from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ReturnItemSchema(BaseModel):
    id: int
    sku_id: Optional[int] = None
    quantity: Optional[int] = None
    reason: Optional[str] = None
    price: Optional[float] = None
    
    class Config:
        from_attributes = True

class ReturnSchema(BaseModel):
    id: int
    shop_id: Optional[int] = None
    uzum_return_id: Optional[int] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    items: List[ReturnItemSchema] = []

    class Config:
        from_attributes = True
