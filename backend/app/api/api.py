from fastapi import APIRouter
from app.api.endpoints import auth, products, orders, finance, fbs, invoices, returns, sync, settings, shops

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(shops.router, prefix="/shops", tags=["shops"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(finance.router, prefix="/finance", tags=["finance"])
api_router.include_router(fbs.router, prefix="/fbs", tags=["fbs"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
api_router.include_router(returns.router, prefix="/returns", tags=["returns"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
