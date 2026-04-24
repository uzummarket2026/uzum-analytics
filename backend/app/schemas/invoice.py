from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class InvoiceItemSchema(BaseModel):
    id: int
    sku_id: Optional[int] = None
    quantity: Optional[int] = None
    
    class Config:
        from_attributes = True

class InvoiceSchema(BaseModel):
    id: int
    shop_id: Optional[int] = None
    uzum_invoice_id: Optional[int] = None
    status: Optional[str] = None
    invoice_type: Optional[str] = None
    created_at: Optional[datetime] = None
    items: List[InvoiceItemSchema] = []

    class Config:
        from_attributes = True
