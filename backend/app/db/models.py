from sqlalchemy import Column, Integer, BigInteger, String, Boolean, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    uzum_shop_id = Column(BigInteger, unique=True, index=True)
    name = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    
    products = relationship("Product", back_populates="shop")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"))
    uzum_product_id = Column(BigInteger, index=True)
    sku_id = Column(BigInteger, unique=True, index=True)
    sku_code = Column(String, index=True)
    title = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    purchase_price = Column(Float)
    commission_percent = Column(Float) # Komissiya foizi
    stock = Column(Integer)
    fbo_stock = Column(Integer, default=0)
    fbs_stock = Column(Integer, default=0)
    image_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    shop = relationship("Shop", back_populates="products")
    orders = relationship("Order", back_populates="product")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    uzum_order_id = Column(BigInteger, unique=True, index=True)
    main_order_id = Column(BigInteger, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    uzum_shop_id = Column(BigInteger, nullable=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    quantity = Column(Integer)
    amount_returns = Column(Integer, default=0)
    cancelled = Column(Integer, default=0)
    total_price = Column(Float)
    purchase_price = Column(Float)
    commission_amount = Column(Float)
    logistic_fee = Column(Float)
    seller_profit = Column(Float)
    withdrawn_profit = Column(Float, default=0)
    sku_code = Column(String, index=True)
    sku_title = Column(String)
    sku_char_title = Column(String)
    sku_char_value = Column(String)
    status = Column(String, default="pending")
    order_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="orders")
    shop = relationship("Shop")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"))
    uzum_payment_id = Column(BigInteger, unique=True, index=True, nullable=True)
    amount = Column(Float)
    name = Column(String)
    description = Column(String)
    date = Column(DateTime(timezone=True))
    source = Column(String)
    payment_type = Column(String)
    status = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"))
    uzum_invoice_id = Column(BigInteger, unique=True, index=True)
    status = Column(String)
    invoice_type = Column(String) # supply, return
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FbsOrder(Base):
    __tablename__ = "fbs_orders"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"))
    uzum_order_id = Column(BigInteger, unique=True, index=True)
    status = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Return(Base):
    __tablename__ = "returns"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"))
    uzum_return_id = Column(BigInteger, unique=True, index=True)
    status = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    shop = relationship("Shop")
    items = relationship("ReturnItem", back_populates="return_obj")

class ReturnItem(Base):
    __tablename__ = "return_items"

    id = Column(Integer, primary_key=True, index=True)
    return_id = Column(Integer, ForeignKey("returns.id"))
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    sku_id = Column(BigInteger, index=True)
    quantity = Column(Integer)
    reason = Column(String)
    price = Column(Float)

    return_obj = relationship("Return", back_populates="items")
    product = relationship("Product")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    sku_id = Column(BigInteger, index=True)
    quantity = Column(Integer)
    
    invoice = relationship("Invoice", backref="items")
    product = relationship("Product")

class SystemSetting(Base):
    __tablename__ = "system_settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)


