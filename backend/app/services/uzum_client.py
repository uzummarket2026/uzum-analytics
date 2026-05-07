"""Uzum Seller OpenAPI klienti.

Barcha endpointlar `uzum_market_api.json` (single source of truth) dan
`uzum_endpoints.py` orqali olinadi. Yangi endpoint kerak bo'lsa:
  1) JSON spec'ga qo'shing
  2) Bu yerda operationId bo'yicha metod qo'shing
"""
import requests
from typing import Dict, Any, Optional, List

from app.services.uzum_endpoints import op, path_for


class UzumForbiddenError(Exception):
    """Do'kon mavjud bo'lmaganda tashlanadigan xato"""
    pass


class UzumClient:
    BASE_URL = "https://api-seller.uzum.uz/api/seller-openapi"

    def __init__(self, api_token: str):
        self.headers = {
            "Authorization": api_token,
            "Content-Type": "application/json",
            "Accept-Language": "uz",
        }
        self.timeout = 30

    # ---------- low-level ----------

    def _request(self, op_id: str, *, path_params: Optional[dict] = None,
                 params: Optional[dict] = None, json_data: Optional[dict] = None) -> Optional[Any]:
        method, _ = op(op_id)
        path = path_for(op_id, **(path_params or {}))
        url = f"{self.BASE_URL}{path}"

        response = None
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=json_data,
                timeout=self.timeout,
            )
            response.raise_for_status()
            if not response.text:
                return True
            data = response.json()
            if isinstance(data, dict) and "payload" in data:
                return data["payload"]
            return data
        except requests.exceptions.RequestException as e:
            if response is not None:
                try:
                    err = response.json()
                    if err.get("errors") and any(
                        x.get("code") == "forbidden-001" for x in err["errors"]
                    ):
                        raise UzumForbiddenError(f"Shop is not available: {op_id}")
                except UzumForbiddenError:
                    raise
                except Exception:
                    pass
            print(f"Uzum API xato [{op_id}]: {e}")
            if response is not None:
                print(f"Response: {response.text}")
            return None

    # ---------- Shops ----------

    def get_shops(self) -> List[Dict[str, Any]]:
        """getOwnedShops — GET /v1/shops"""
        data = self._request("getOwnedShops")
        if isinstance(data, dict) and "payload" in data:
            return data["payload"]
        return data if isinstance(data, list) else []

    # ---------- Products ----------

    def get_products_by_shop(self, shop_id: int, page: int = 0, size: int = 100) -> Optional[Dict[str, Any]]:
        """getShopProductsByShopId — GET /v1/product/shop/{shopId}"""
        return self._request(
            "getShopProductsByShopId",
            path_params={"shopId": shop_id},
            params={"page": page, "size": size},
        )

    def update_prices(self, shop_id: int, price_data: dict) -> bool:
        """saveProductPriceData — POST /v1/product/{shopId}/sendPriceData"""
        return bool(self._request(
            "saveProductPriceData",
            path_params={"shopId": shop_id},
            json_data=price_data,
        ))

    # ---------- Finance / Orders / Expenses ----------

    def get_orders(
        self,
        shop_ids: List[int],
        date_from: Optional[int] = None,
        date_to: Optional[int] = None,
        page: int = 0,
        size: int = 50,
        statuses: Optional[List[str]] = None,
        group: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """getFinanceOrders — GET /v1/finance/orders

        statuses: TO_WITHDRAW | PROCESSING | CANCELED | PARTIALLY_CANCELLED
        group=True → ProductGroupedSellerItem; False → SellerOrderItemDto
        """
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
        return self._request("getFinanceOrders", params=params)

    def get_expenses(self, shop_ids: List[int], date_from: Optional[int] = None,
                     date_to: Optional[int] = None, page: int = 0, size: int = 50) -> Optional[Dict[str, Any]]:
        """getFinanceExpenses — GET /v1/finance/expenses"""
        params: Dict[str, Any] = {"shopIds": shop_ids, "page": page, "size": size}
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        return self._request("getFinanceExpenses", params=params)

    # ---------- Invoices (supply) ----------

    def get_invoices(self, shop_id: int, page: int = 0, size: int = 50) -> Optional[Dict[str, Any]]:
        """getShopInvoicesByShopId — GET /v1/shop/{shopId}/invoice"""
        return self._request(
            "getShopInvoicesByShopId",
            path_params={"shopId": shop_id},
            params={"page": page, "size": size},
        )

    def get_invoice_products(self, shop_id: int, invoice_id: int) -> Optional[List[Dict[str, Any]]]:
        """getShopInvoiceProductsByShopId — GET /v1/shop/{shopId}/invoice/products"""
        return self._request(
            "getShopInvoiceProductsByShopId",
            path_params={"shopId": shop_id},
            params={"invoiceId": invoice_id},
        )

    def get_seller_invoices(self, page: int = 0, size: int = 50) -> List[Dict[str, Any]]:
        """getSellerInvoice — GET /v1/invoice"""
        data = self._request("getSellerInvoice", params={"page": page, "size": size})
        return data if isinstance(data, list) else []

    # ---------- Returns ----------

    def get_returns(self, shop_id: int, page: int = 0, size: int = 20) -> Optional[Dict[str, Any]]:
        """getShopReturnsByShopId — GET /v1/shop/{shopId}/return"""
        return self._request(
            "getShopReturnsByShopId",
            path_params={"shopId": shop_id},
            params={"page": page, "size": size},
        )

    def get_return_items(self, shop_id: int, return_id: int) -> Optional[Dict[str, Any]]:
        """getShopReturnByShopIdAndReturnId — GET /v1/shop/{shopId}/return/{returnId}"""
        return self._request(
            "getShopReturnByShopIdAndReturnId",
            path_params={"shopId": shop_id, "returnId": return_id},
        )

    def get_all_returns(self, return_id: Optional[int] = None,
                        page: int = 0, size: int = 50) -> Optional[Any]:
        """getSellerReturn — GET /v1/return"""
        params: Dict[str, Any] = {"page": page, "size": size}
        if return_id is not None:
            params["returnId"] = return_id
        return self._request("getSellerReturn", params=params)

    # ---------- FBS Orders ----------

    def get_fbs_orders(self, shop_ids: List[int], status: str = "CREATED",
                       page: int = 0, size: int = 50) -> Optional[Dict[str, Any]]:
        """getFbsOrdersV2 — GET /v2/fbs/orders"""
        params = {"shopIds": shop_ids, "status": status, "page": page, "size": size}
        return self._request("getFbsOrdersV2", params=params)

    def get_fbs_orders_count(self, shop_ids: List[int], status: Optional[str] = None,
                             date_from: Optional[int] = None, date_to: Optional[int] = None) -> Optional[Any]:
        """getOrderCountV2 — GET /v2/fbs/orders/count"""
        params: Dict[str, Any] = {"shopIds": shop_ids}
        if status:
            params["status"] = status
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        return self._request("getOrderCountV2", params=params)

    def get_fbs_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """getFbsOrderByOrderId — GET /v1/fbs/order/{orderId}"""
        return self._request("getFbsOrderByOrderId", path_params={"orderId": order_id})

    def confirm_fbs_order(self, order_id: int) -> bool:
        """confirmFbsOrder — POST /v1/fbs/order/{orderId}/confirm"""
        return bool(self._request("confirmFbsOrder", path_params={"orderId": order_id}))

    CANCEL_REASONS = {
        "OUT_OF_STOCK", "CUSTOMER_REQUEST", "WRONG_ADDRESS", "DEFECTED", "OTHER",
    }

    def cancel_fbs_order(self, order_id: int, reason: str, comment: Optional[str] = None) -> bool:
        """cancelFbsOrder — POST /v1/fbs/order/{orderId}/cancel"""
        if reason not in self.CANCEL_REASONS:
            raise ValueError(f"Invalid reason '{reason}'. Allowed: {sorted(self.CANCEL_REASONS)}")
        body: Dict[str, Any] = {"reason": reason}
        if comment:
            body["comment"] = comment
        return bool(self._request("cancelFbsOrder", path_params={"orderId": order_id}, json_data=body))

    def get_fbs_order_return_reasons(self) -> Optional[Any]:
        """getFbsReturnReasons — GET /v1/fbs/order/return-reasons"""
        return self._request("getFbsReturnReasons")

    def get_fbs_order_labels(self, order_id: int, size: str) -> Optional[Any]:
        """fbsPrintLabel — GET /v1/fbs/order/{orderId}/labels/print"""
        return self._request("fbsPrintLabel", path_params={"orderId": order_id}, params={"size": size})

    # ---------- FBS Stocks ----------

    def get_fbs_stocks(self) -> Optional[Any]:
        """downloadFbsSkuStocks — GET /v2/fbs/sku/stocks"""
        return self._request("downloadFbsSkuStocks")

    def update_fbs_stocks(self, stock_data: dict) -> bool:
        """uploadSkuAmounts — POST /v2/fbs/sku/stocks"""
        return bool(self._request("uploadSkuAmounts", json_data=stock_data))

    # ---------- FBS Invoices ----------

    def get_fbs_invoices(self, statuses: List[str], page: int = 0, size: int = 50) -> Optional[Any]:
        """getFbsInvoices_1 — GET /v1/fbs/invoice"""
        return self._request("getFbsInvoices_1", params={"statuses": statuses, "page": page, "size": size})

    def create_fbs_invoice(self, body: dict) -> Optional[Any]:
        """create — POST /v1/fbs/invoice"""
        return self._request("create", json_data=body)

    def get_fbs_invoice(self, invoice_id: int) -> Optional[Any]:
        """getFbsInvoice_byId — GET /v1/fbs/invoice/{invoiceId}"""
        return self._request("getFbsInvoice_byId", path_params={"invoiceId": invoice_id})

    def get_fbs_invoice_orders(self, invoice_id: int) -> Optional[Any]:
        """getFbsOrdersByInvoiceId — GET /v1/fbs/invoice/{invoiceId}/orders"""
        return self._request("getFbsOrdersByInvoiceId", path_params={"invoiceId": invoice_id})

    def get_fbs_invoice_closing_documents(self, invoice_id: int) -> Optional[Any]:
        """getFbsInvoiceClosingDocuments — GET /v1/fbs/invoice/{invoiceId}/closing-documents"""
        return self._request("getFbsInvoiceClosingDocuments", path_params={"invoiceId": invoice_id})

    def update_fbs_invoice_content(self, invoice_id: int, body: dict) -> Optional[Any]:
        """updateFbsInvoice — POST /v1/fbs/invoice/{invoiceId}/update-content"""
        return self._request("updateFbsInvoice", path_params={"invoiceId": invoice_id}, json_data=body)

    def cancel_fbs_invoice(self, invoice_id: int) -> Optional[Any]:
        """fbsInvoiceCancel — POST /v1/fbs/invoice/{invoiceId}/cancel"""
        return self._request("fbsInvoiceCancel", path_params={"invoiceId": invoice_id})

    def get_fbs_invoice_time_slots(self, dop_id: str, seller_order_ids: List[int]) -> Optional[Any]:
        """getFbsInvoiceTimeSlots — GET /v1/fbs/invoice/dop/time-slot"""
        return self._request("getFbsInvoiceTimeSlots",
                             params={"dopId": dop_id, "sellerOrderIds": seller_order_ids})

    def set_fbs_invoice_time_slot(self, body: dict) -> Optional[Any]:
        """updateDropOffPointAndTimeSlot — POST /v1/fbs/invoice/dop/time-slot"""
        return self._request("updateDropOffPointAndTimeSlot", json_data=body)

    def get_fbs_invoice_drop_off_points(self, customer_order_ids: List[int]) -> Optional[Any]:
        """getFbsInvoiceDropOffPoints — GET /v1/fbs/invoice/dop/drop-off-points"""
        return self._request("getFbsInvoiceDropOffPoints",
                             params={"customerOrderIds": customer_order_ids})

    def get_fbs_invoice_print(self, invoice_id: int) -> Optional[Any]:
        """printFbsInvoice — GET /v1/fbs/invoice/{invoiceId}/print"""
        return self._request("printFbsInvoice", path_params={"invoiceId": invoice_id})
