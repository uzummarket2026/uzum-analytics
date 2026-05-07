"""Uzum API endpoint registry — uzum_market_api.json'dan yuklanadi.

uzum_market_api.json — barcha endpointlar uchun yagona haqqoniy manba (template).
Yangi endpoint qo'shilsa yoki path o'zgarsa, faqat shu JSON faylga o'zgartirish
kiritiladi — UzumClient avtomatik yangi yo'l/usulni ko'radi.

Foydalanish:
    from app.services.uzum_endpoints import op, path_for

    method, path = op("getFinanceOrders")        # ("GET", "/v1/finance/orders")
    p = path_for("getShopReturnsByShopId", shopId=42)  # "/v1/shop/42/return"
"""
import json
import os
from functools import lru_cache
from typing import Dict, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
SPEC_PATH = os.path.join(_HERE, "uzum_market_api.json")

HTTP_METHODS = {"get", "post", "put", "delete", "patch"}


@lru_cache(maxsize=1)
def load_operations() -> Dict[str, Tuple[str, str]]:
    """operationId -> (METHOD, path) xaritasi."""
    with open(SPEC_PATH, encoding="utf-8") as f:
        spec = json.load(f)

    ops: Dict[str, Tuple[str, str]] = {}
    for path, methods in spec.get("paths", {}).items():
        for method, operation in methods.items():
            if method.lower() not in HTTP_METHODS:
                continue
            op_id = operation.get("operationId")
            if not op_id:
                continue
            ops[op_id] = (method.upper(), path)
    return ops


def op(op_id: str) -> Tuple[str, str]:
    """operationId bo'yicha (METHOD, path) qaytaradi."""
    ops = load_operations()
    if op_id not in ops:
        raise KeyError(f"uzum_market_api.json'da operationId topilmadi: {op_id}")
    return ops[op_id]


def path_for(op_id: str, **path_params) -> str:
    """operationId path'ini olib, {param} larni almashtiradi."""
    _, path = op(op_id)
    for k, v in path_params.items():
        placeholder = "{" + k + "}"
        if placeholder not in path:
            raise KeyError(f"{op_id} path'ida {{{k}}} yo'q: {path}")
        path = path.replace(placeholder, str(v))
    if "{" in path:
        missing = path[path.index("{") + 1 : path.index("}")]
        raise ValueError(f"{op_id} path'ida to'ldirilmagan parametr: {{{missing}}}")
    return path
