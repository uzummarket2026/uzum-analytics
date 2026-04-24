import requests
import requests
from typing import Dict, Any, Optional, List

class UzumForbiddenError(Exception):
    """Do'kon mavjud bo'lmaganda tashlanadigan xato"""
    pass

class UzumClient:
    def __init__(self, api_token: str):
        self.base_url = "https://api-seller.uzum.uz/api/seller-openapi"
        self.headers = {
            "Authorization": api_token,
            "Content-Type": "application/json",
            "Accept-Language": "uz"
        }
        self.timeout = 30

    def _get(self, endpoint: str, params: dict = None) -> Optional[Any]:
        response = None
        try:
            response = requests.get(f"{self.base_url}{endpoint}", headers=self.headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            json_data = response.json()
            if isinstance(json_data, dict) and "payload" in json_data:
                return json_data["payload"]
            return json_data
        except requests.exceptions.RequestException as e:
            if response is not None:
                try:
                    error_data = response.json()
                    if error_data.get("errors") and any(err.get("code") == "forbidden-001" for err in error_data["errors"]):
                        raise UzumForbiddenError(f"Shop is not available: {endpoint}")
                except UzumForbiddenError:
                    raise
                except:
                    pass
            
            print(f"Uzum API xatolik ({endpoint}): {e}")
            if response is not None:
                print(f"Response: {response.text}")
            return None

    def get_shops(self) -> List[Dict[str, Any]]:
        """O'ziga tegishli do'konlar ro'yxatini olish"""
        data = self._get("/v1/shops")
        if isinstance(data, dict) and "payload" in data:
            return data["payload"]
        return data if isinstance(data, list) else []

    def get_products_by_shop(self, shop_id: int, page: int = 0, size: int = 100) -> Optional[Dict[str, Any]]:
        """ID bo'yicha do'konning mahsulotlarini olish (V1)"""
        endpoint = f"/v1/product/shop/{shop_id}"
        params = {"page": page, "size": size}
        print(f"DEBUG: Uzum API dan mahsulotlar o'qilmoqda: shop_id={shop_id}, page={page}")
        return self._get(endpoint, params=params)

    def get_orders(
        self,
        shop_ids: List[int],
        date_from: int = None,
        date_to: int = None,
        page: int = 0,
        size: int = 50,
        statuses: Optional[List[str]] = None,
        group: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Buyurtmalar ro'yxatini olish (Finance Orders).

        statuses: TO_WITHDRAW | PROCESSING | CANCELED | PARTIALLY_CANCELLED
        group: True => orderItems > items (SKU bo'yicha guruhlangan)
        """
        endpoint = "/v1/finance/orders"
        params: Dict[str, Any] = {
            "shopIds": shop_ids,
            "page": page,
            "size": size,
            "group": str(group).lower(),
        }
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        if statuses:
            params["statuses"] = statuses
        return self._get(endpoint, params=params)

    def get_fbs_orders(self, shop_ids: List[int], status: str = "CREATED", page: int = 0, size: int = 50) -> Optional[Dict[str, Any]]:
        """FBS Buyurtmalarini olish"""
        endpoint = "/v2/fbs/orders"
        params = {
            "shopIds": shop_ids,
            "status": status,
            "page": page,
            "size": size
        }
        return self._get(endpoint, params=params)

    def _post(self, endpoint: str, json_data: dict = None) -> Optional[Any]:
        try:
            response = requests.post(f"{self.base_url}{endpoint}", headers=self.headers, json=json_data, timeout=self.timeout)
            response.raise_for_status()
            if response.text:
                return response.json()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Uzum API POST xatolik ({endpoint}): {e}")
            return None

    def get_expenses(self, shop_ids: List[int], date_from: int = None, date_to: int = None, page: int = 0, size: int = 50) -> Optional[Dict[str, Any]]:
        endpoint = "/v1/finance/expenses"
        params = {"shopIds": shop_ids, "page": page, "size": size}
        if date_from: params["dateFrom"] = date_from
        if date_to: params["dateTo"] = date_to
        return self._get(endpoint, params=params)

    def get_invoices(self, shop_id: int, page: int = 0, size: int = 50) -> Optional[Dict[str, Any]]:
        endpoint = f"/v1/shop/{shop_id}/invoice"
        params = {"page": page, "size": size}
        return self._get(endpoint, params=params)

    def get_returns(self, shop_id: int, page: int = 0, size: int = 20) -> Optional[Dict[str, Any]]:
        endpoint = f"/v1/shop/{shop_id}/return"
        params = {"page": page, "size": size}
        return self._get(endpoint, params=params)

    def get_return_items(self, shop_id: int, return_id: int) -> Optional[Dict[str, Any]]:
        endpoint = f"/v1/shop/{shop_id}/return/{return_id}"
        return self._get(endpoint)

    def get_invoice_products(self, shop_id: int, invoice_id: int) -> Optional[List[Dict[str, Any]]]:
        endpoint = f"/v1/shop/{shop_id}/invoice/products"
        params = {"invoiceId": invoice_id}
        return self._get(endpoint, params=params)

    def get_fbs_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        endpoint = f"/v1/fbs/order/{order_id}"
        return self._get(endpoint)

    def confirm_fbs_order(self, order_id: int) -> bool:
        endpoint = f"/v1/fbs/order/{order_id}/confirm"
        return bool(self._post(endpoint))

    CANCEL_REASONS = {
        "OUT_OF_STOCK",
        "CUSTOMER_REQUEST",
        "WRONG_ADDRESS",
        "DEFECTED",
        "OTHER",
    }

    def cancel_fbs_order(self, order_id: int, reason: str, comment: Optional[str] = None) -> bool:
        if reason not in self.CANCEL_REASONS:
            raise ValueError(
                f"Invalid reason '{reason}'. Allowed: {sorted(self.CANCEL_REASONS)}"
            )
        endpoint = f"/v1/fbs/order/{order_id}/cancel"
        payload: Dict[str, Any] = {"reason": reason}
        if comment:
            payload["comment"] = comment
        return bool(self._post(endpoint, json_data=payload))

    def update_prices(self, shop_id: int, price_data: dict) -> bool:
        endpoint = f"/v1/product/{shop_id}/sendPriceData"
        return bool(self._post(endpoint, json_data=price_data))

    def update_fbs_stocks(self, stock_data: dict) -> bool:
        endpoint = "/v2/fbs/sku/stocks"
        return bool(self._post(endpoint, json_data=stock_data))
