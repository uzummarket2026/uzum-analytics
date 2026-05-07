from app.db.session import SessionLocal
from app.db.models import Product, Order, Shop, Expense, Invoice, FbsOrder, Return, ReturnItem, InvoiceItem, SystemSetting
from app.core.config import settings
from app.services.uzum_client import UzumClient, UzumForbiddenError
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_api_token(db, user_id: int) -> str:
    """Foydalanuvchining shaxsiy Uzum API tokeni."""
    setting = db.query(SystemSetting).filter(
        SystemSetting.user_id == user_id,
        SystemSetting.key == "uzum_api_token",
    ).first()
    if setting and setting.value:
        return setting.value
    return ""

def safe_float(value, default=0.0):
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_url(url_data):
    """Uzum rasm URL'ini standart formatga keltirish."""
    if not url_data:
        return None

    if isinstance(url_data, dict):
        url_data = url_data.get("high") or url_data.get("low") or url_data.get("photoKey") or url_data.get("url")

    if isinstance(url_data, str):
        url_data = url_data.strip()
        if not url_data:
            return None

        if url_data.startswith("https://") or url_data.startswith("http://"):
            res = url_data
        elif url_data.startswith("//"):
            res = f"https:{url_data}"
        elif "/" not in url_data:
            return f"https://images.uzum.uz/{url_data}/t_product_540_high.jpg"
        elif url_data.startswith("/"):
            res = f"https://images.uzum.uz{url_data}"
        else:
            res = f"https://images.uzum.uz/{url_data}"

        if "images.uzum.uz" in res and not any(ext in res.lower() for ext in [".jpg", ".png", ".jpeg", ".webp"]):
            if not res.endswith("/"):
                res += "/"
            res += "t_product_540_high.jpg"
        return res

    return str(url_data) if url_data else None

def sync_uzum_data_task(user_id: int) -> str:
    """Foydalanuvchining do'konlari va mahsulotlarini sinxronlash."""
    db = SessionLocal()
    try:
        logger.info(f"Sinxronizatsiya boshlandi (user={user_id}): {datetime.now()}")
        token = get_api_token(db, user_id)
        if not token:
            logger.error(f"XATO: user {user_id} uchun Uzum API token topilmadi!")
            return "Token topilmadi"

        client = UzumClient(token)

        # 1. Sync Shops (faqat shu user'ga tegishli)
        try:
            shops_data = client.get_shops()
            logger.info(f"API dan kelgan do'konlar soni: {len(shops_data) if shops_data else 0}")

            if not shops_data:
                logger.warning("OGOHLANTIRISH: Do'konlar ro'yxati bo'sh keldi.")

            # Bu user'ning shoplarini avval is_active=False qilamiz
            db.query(Shop).filter(Shop.user_id == user_id).update({Shop.is_active: False})

            for shop_info in shops_data:
                shop_id = shop_info.get("id")
                name = shop_info.get("name", "Unknown Shop")
                logger.info(f"Do'kon saqlanmoqda: {name} (ID: {shop_id})")

                shop = db.query(Shop).filter(
                    Shop.user_id == user_id,
                    Shop.uzum_shop_id == shop_id,
                ).first()
                if not shop:
                    shop = Shop(user_id=user_id, uzum_shop_id=shop_id, name=name, is_active=True)
                    db.add(shop)
                else:
                    shop.name = name
                    shop.is_active = True
            db.commit()
        except Exception as e:
            logger.error(f"Do'konlarni sinxronlashda xato: {e}")

        product_sync_count = 0
        db_shops = db.query(Shop).filter(
            Shop.user_id == user_id,
            Shop.is_active == True,
        ).all()
        logger.info(f"Faol do'konlar soni: {len(db_shops)}")
        
        for shop in db_shops:
            try:
                page = 0
                while page < 500: # Xavfsizlik uchun chegara
                    print(f"[{shop.name}] Sahifa {page} mahsulotlari o'qilmoqda...")
                    products_data = None
                    for attempt in range(3): # 3 marta urinish
                        try:
                            products_data = client.get_products_by_shop(shop_id=shop.uzum_shop_id, page=page, size=100)
                            if products_data: break
                        except Exception as e:
                            print(f"Sahifa {page} ni olishda xato (urinish {attempt+1}): {e}")
                            time.sleep(1)
                    
                    if not products_data or 'productList' not in products_data:
                        print(f"[{shop.name}] Sahifa {page} da ma'lumot yo'q yoki tugadi.")
                        break
                        
                    current_batch = products_data.get('productList', [])
                    if not current_batch:
                        break
                        
                    print(f"[{shop.name}] Sahifa {page}: {len(current_batch)} ta mahsulot keldi.")
                    
                    for p_card in current_batch:
                        product_title = p_card.get("title", "Unknown")
                        uzum_product_id = p_card.get("productId")
                        product_main_image = safe_url(p_card.get("image") or p_card.get("previewImg"))
                        
                        sku_items = p_card.get('skuList', [])
                        for sku_data in sku_items:
                            sku_id = sku_data.get("skuId")
                            if not sku_id: continue
                            
                            sku_title = sku_data.get("skuFullTitle") or sku_data.get("skuTitle") or product_title
                            sku_code = sku_data.get("article") or sku_data.get("sellerItemCode") or str(sku_id)
                            sku_image = safe_url(sku_data.get("previewImage") or sku_data.get("previewImg")) or product_main_image
                            
                            price = safe_float(sku_data.get("price"), 0)
                            # Tannarxni to'g'ridan-to'g'ri mahsulot shablonidan o'qiymiz
                            purchase_price = safe_float(sku_data.get("purchasePrice"), 0)
                            commission_percent = safe_float(sku_data.get("commission"), 0)
                            
                            fbo_stock = safe_int(sku_data.get("quantityActive"), 0)
                            fbs_stock = safe_int(sku_data.get("quantityFbs"), 0)
                            stock = fbo_stock + fbs_stock
                            
                            product = db.query(Product).filter(
                                Product.user_id == user_id,
                                Product.sku_id == sku_id,
                            ).first()
                            if product:
                                product.stock = stock
                                product.fbo_stock = fbo_stock
                                product.fbs_stock = fbs_stock
                                product.price = price
                                if purchase_price > 0:
                                    product.purchase_price = purchase_price
                                product.commission_percent = commission_percent
                                product.title = sku_title
                                product.sku_code = sku_code
                                product.uzum_product_id = uzum_product_id
                                product.shop_id = shop.id
                                product.image_url = sku_image
                            else:
                                product = Product(
                                    user_id=user_id,
                                    shop_id=shop.id,
                                    uzum_product_id=uzum_product_id,
                                    sku_id=sku_id,
                                    sku_code=sku_code,
                                    title=sku_title,
                                    price=price,
                                    purchase_price=purchase_price,
                                    commission_percent=commission_percent,
                                    stock=stock,
                                    fbo_stock=fbo_stock,
                                    fbs_stock=fbs_stock,
                                    image_url=sku_image,
                                )
                                db.add(product)
                            product_sync_count += 1
                    
                    if len(current_batch) < 100:
                        break
                    page += 1
                
                db.commit()
            except UzumForbiddenError:
                shop.is_active = False
                db.commit()
            except Exception as e:
                logger.error(f"Shop {shop.id} mahsulotlarida xato: {e}")
                db.rollback()
                
        return f"Sinxronizatsiya: {product_sync_count} mahsulot."
    finally:
        db.close()

# Invoice-based backfill functions removed as they cause high DB load and are not the primary way.


ORDER_STATUSES = ["TO_WITHDRAW", "PROCESSING", "CANCELED", "PARTIALLY_CANCELLED"]


def _upsert_order_item(db, o: dict, shop_map: dict, user_id: int) -> str:
    """Bitta orderItem'ni saqlash. Qaytaradi: 'inserted' | 'updated' | 'skipped'."""
    item_id = o.get("id")
    if not item_id:
        return "skipped"

    main_order_id = o.get("orderId")
    uzum_product_id = o.get("productId")
    uzum_shop_id_val = o.get("shopId")
    local_shop_id = shop_map.get(uzum_shop_id_val)

    status = (o.get("status") or "PENDING").lower()
    quantity = safe_int(o.get("amount"), 1)
    amount_returns = safe_int(o.get("amountReturns"), 0)
    cancelled = safe_int(o.get("cancelled"), 0)

    seller_price = safe_float(o.get("sellerPrice"), 0)
    purchase_price = safe_float(o.get("purchasePrice"), 0)
    commission_amount = safe_float(o.get("commission"), 0)
    logistic_fee = safe_float(o.get("logisticDeliveryFee"), 0)
    seller_profit = safe_float(o.get("sellerProfit"), 0)
    withdrawn_profit = safe_float(o.get("withdrawnProfit"), 0)

    sku_title = o.get("skuTitle")
    sku_char_title = o.get("skuCharTitle")
    sku_char_value = o.get("skuCharValue")

    net_qty = max(quantity - amount_returns - cancelled, 0)
    total_price = float(seller_price * net_qty)

    # Uzum kabinet "dateIssued" (rasmiylashtirilgan vaqt) ni ko'rsatadi.
    # "date" — buyurtma yaratilgan vaqt (~1 daqiqa oldinroq).
    date_ms = o.get("dateIssued") or o.get("date")
    order_date = datetime.fromtimestamp(date_ms / 1000.0) if date_ms else None

    product = None
    if uzum_product_id:
        q = db.query(Product).filter(
            Product.user_id == user_id,
            Product.uzum_product_id == uzum_product_id,
        )
        if sku_title:
            product = q.filter(Product.title == sku_title).first() or q.first()
        else:
            product = q.first()

    product_id = product.id if product else None
    sku_code = product.sku_code if product else None

    order = db.query(Order).filter(
        Order.user_id == user_id,
        Order.uzum_order_id == item_id,
    ).first()
    if order is None:
        db.add(Order(
            user_id=user_id,
            uzum_order_id=item_id,
            main_order_id=main_order_id,
            shop_id=local_shop_id,
            uzum_shop_id=uzum_shop_id_val,
            product_id=product_id,
            quantity=quantity,
            amount_returns=amount_returns,
            cancelled=cancelled,
            total_price=total_price,
            purchase_price=purchase_price,
            commission_amount=commission_amount,
            logistic_fee=logistic_fee,
            seller_profit=seller_profit,
            withdrawn_profit=withdrawn_profit,
            sku_code=sku_code,
            sku_title=sku_title,
            sku_char_title=sku_char_title,
            sku_char_value=sku_char_value,
            status=status,
            order_date=order_date,
        ))
        return "inserted"

    order.main_order_id = main_order_id
    order.shop_id = local_shop_id
    order.uzum_shop_id = uzum_shop_id_val
    if product_id:
        order.product_id = product_id
    order.quantity = quantity
    order.amount_returns = amount_returns
    order.cancelled = cancelled
    # Pul/SKU fieldlari: null/0 kelsa eski qiymatni saqlaymiz
    # (API ba'zi statuslarda bu qiymatlarni qaytarmaydi)
    if total_price > 0:
        order.total_price = total_price
    if purchase_price > 0:
        order.purchase_price = purchase_price
    if commission_amount > 0:
        order.commission_amount = commission_amount
    if logistic_fee > 0:
        order.logistic_fee = logistic_fee
    if seller_profit > 0:
        order.seller_profit = seller_profit
    if withdrawn_profit > 0:
        order.withdrawn_profit = withdrawn_profit
    if sku_code:
        order.sku_code = sku_code
    if sku_title:
        order.sku_title = sku_title
    if sku_char_title:
        order.sku_char_title = sku_char_title
    if sku_char_value:
        order.sku_char_value = sku_char_value
    order.status = status
    if order_date:
        order.order_date = order_date
    return "updated"


def sync_uzum_orders_task(user_id: int) -> str:
    """Foydalanuvchining barcha do'konlaridan buyurtmalarni sinxronlash."""
    db = SessionLocal()
    try:
        token = get_api_token(db, user_id)
        if not token:
            logger.error(f"Order sync (user={user_id}): API token topilmadi")
            return "Token topilmadi"

        client = UzumClient(api_token=token)
        shops = db.query(Shop).filter(
            Shop.user_id == user_id,
            Shop.is_active == True,
        ).all()
        if not shops:
            return "Do'konlar yo'q."

        shop_map = {shop.uzum_shop_id: shop.id for shop in shops}
        uzum_shop_ids = list(shop_map.keys())

        PAGE_SIZE = 100
        MAX_PAGES = 10000
        EMPTY_RETRIES = 2

        totals = {"inserted": 0, "updated": 0, "skipped": 0}
        seen_ids = set()
        pages_total = 0

        for status in ORDER_STATUSES:
            page = 0
            empty_in_a_row = 0
            status_count = 0

            while page < MAX_PAGES:
                try:
                    resp = client.get_orders(
                        shop_ids=uzum_shop_ids,
                        page=page,
                        size=PAGE_SIZE,
                        group=False,
                        statuses=[status],
                    )
                except Exception as e:
                    logger.error(f"Order sync [{status}]: page {page} xato: {e}")
                    break

                items = (resp or {}).get("orderItems") or []
                pages_total += 1

                if not items:
                    empty_in_a_row += 1
                    if empty_in_a_row >= EMPTY_RETRIES:
                        break
                    page += 1
                    time.sleep(0.2)
                    continue
                empty_in_a_row = 0

                for o in items:
                    item_id = o.get("id")
                    if not item_id or item_id in seen_ids:
                        totals["skipped"] += 1
                        continue
                    seen_ids.add(item_id)
                    result = _upsert_order_item(db, o, shop_map, user_id)
                    totals[result] = totals.get(result, 0) + 1
                    status_count += 1

                try:
                    db.commit()
                except Exception as e:
                    logger.error(f"Order sync [{status}]: page {page} commit xato: {e}")
                    db.rollback()

                if len(items) < PAGE_SIZE:
                    break
                page += 1
                time.sleep(0.1)

            logger.info(f"Order sync [{status}]: {status_count} item, {page+1} sahifa")

        logger.info(
            f"Order sync tugadi: {totals['inserted']} yangi, "
            f"{totals['updated']} yangilandi, {totals['skipped']} o'tkazib yuborildi, "
            f"jami {pages_total} sahifa"
        )
        return f"{totals['inserted']} yangi, {totals['updated']} yangilandi."
    finally:
        db.close()

def sync_expenses_task(user_id: int) -> str:
    db = SessionLocal()
    try:
        token = get_api_token(db, user_id)
        if not token:
            return "Token topilmadi"
        client = UzumClient(api_token=token)
        shops = db.query(Shop).filter(Shop.user_id == user_id, Shop.is_active == True).all()
        uzum_shop_ids = [shop.uzum_shop_id for shop in shops if shop.uzum_shop_id]
        if not uzum_shop_ids:
            return "Do'konlar yo'q."
        expenses_data = client.get_expenses(shop_ids=uzum_shop_ids, size=100)
        
        sync_count = 0
        if expenses_data and 'payments' in expenses_data:
            for e_data in expenses_data['payments']:
                payment_id = e_data.get("id")
                payment_type = (e_data.get("type") or "").upper()
                status = (e_data.get("status") or "").upper()

                if payment_type != "OUTCOME" or status != "CONFIRMED":
                    continue

                shop_id = e_data.get("shopId")
                amount = safe_float(e_data.get("paymentPrice"), 0)
                name = e_data.get("name") or e_data.get("source") or ""
                source = e_data.get("source", "")
                date_ms = e_data.get("dateService") or e_data.get("dateCreated")
                date_val = None
                if date_ms:
                    date_val = datetime.fromtimestamp(date_ms / 1000.0)

                shop = db.query(Shop).filter(
                    Shop.user_id == user_id, Shop.uzum_shop_id == shop_id
                ).first()
                if not shop:
                    continue

                expense = db.query(Expense).filter(
                    Expense.user_id == user_id,
                    Expense.uzum_payment_id == payment_id,
                ).first()
                if expense:
                    expense.amount = amount
                    expense.name = name
                    expense.source = source
                    expense.date = date_val
                    expense.payment_type = payment_type
                    expense.status = status
                else:
                    expense = Expense(
                        user_id=user_id,
                        shop_id=shop.id,
                        uzum_payment_id=payment_id,
                        amount=amount,
                        name=name,
                        description=name,
                        source=source,
                        date=date_val,
                        payment_type=payment_type,
                        status=status,
                    )
                    db.add(expense)
                    sync_count += 1
            db.commit()
        return f"{sync_count} ta xarajat saqlandi."
    finally:
        db.close()

def sync_invoices_task(user_id: int) -> str:
    db = SessionLocal()
    try:
        token = get_api_token(db, user_id)
        if not token:
            return "Token topilmadi"
        client = UzumClient(api_token=token)
        shops = db.query(Shop).filter(Shop.user_id == user_id, Shop.is_active == True).all()
        sync_count = 0
        
        for shop in shops:
            try:
                time.sleep(0.1)
                invoices_data = client.get_invoices(shop_id=shop.uzum_shop_id, size=50)
                if invoices_data and isinstance(invoices_data, list):
                    for inv in invoices_data:
                        inv_id = inv.get("id")
                        invoice_status = inv.get("invoiceStatus") or {}
                        status = (
                            invoice_status.get("value")
                            if isinstance(invoice_status, dict) else None
                        ) or inv.get("status")

                        db_inv = db.query(Invoice).filter(
                            Invoice.user_id == user_id,
                            Invoice.uzum_invoice_id == inv_id,
                        ).first()
                        if not db_inv:
                            db_inv = Invoice(user_id=user_id, shop_id=shop.id, uzum_invoice_id=inv_id, status=status, invoice_type="supply")
                            db.add(db_inv)
                        else:
                            db_inv.status = status
                        sync_count += 1
                    db.commit()
            except UzumForbiddenError as e:
                logger.warning(f"Shop {shop.uzum_shop_id} invoice sync: Shop not available. Marking inactive.")
                shop.is_active = False
                db.commit()
            except Exception as e:
                logger.error(f"Invoice sync error for shop {shop.id}: {e}")
                db.rollback()
        
        return f"{sync_count} ta yukxat sinxronlandi."
    finally:
        db.close()

def sync_returns_task(user_id: int) -> str:
    db = SessionLocal()
    try:
        token = get_api_token(db, user_id)
        if not token:
            return "Token topilmadi"
        client = UzumClient(api_token=token)
        shops = db.query(Shop).filter(Shop.user_id == user_id, Shop.is_active == True).all()
        sync_count = 0
        
        for shop in shops:
            try:
                time.sleep(0.1)
                returns_data = client.get_returns(shop_id=shop.uzum_shop_id, size=50)
                return_list = []
                if returns_data:
                    if isinstance(returns_data, list): 
                        return_list = returns_data
                    elif isinstance(returns_data, dict):
                        # Try different common response structures
                        if "returns" in returns_data:
                            return_list = returns_data["returns"]
                        elif "payload" in returns_data and isinstance(returns_data["payload"], dict):
                            return_list = returns_data["payload"].get("returns", [])
                        elif "payload" in returns_data and isinstance(returns_data["payload"], list):
                            return_list = returns_data["payload"]
                        else:
                            # If it's a dict but none of the above, it might be the item itself or empty
                            return_list = []
                
                if not isinstance(return_list, list):
                    continue

                for ret in return_list:
                    if not isinstance(ret, dict): continue
                    ret_id = ret.get("id")
                    status = ret.get("status")
                    
                    db_ret = db.query(Return).filter(
                        Return.user_id == user_id,
                        Return.uzum_return_id == ret_id,
                    ).first()
                    if not db_ret:
                        db_ret = Return(user_id=user_id, shop_id=shop.id, uzum_return_id=ret_id, status=status)
                        db.add(db_ret)
                    else:
                        db_ret.status = status
                    sync_count += 1
                db.commit()
            except UzumForbiddenError as e:
                logger.warning(f"Shop {shop.uzum_shop_id} returns sync: Shop not available. Marking inactive.")
                shop.is_active = False
                db.commit()
            except Exception as e:
                logger.error(f"Return sync error for shop {shop.id}: {e}")
                db.rollback()
        return f"{sync_count} ta qaytarish sinxronlandi."
    finally:
        db.close()

def sync_fbs_orders_task(user_id: int) -> str:
    db = SessionLocal()
    try:
        token = get_api_token(db, user_id)
        if not token:
            return "Token topilmadi"
        client = UzumClient(api_token=token)
        shops = db.query(Shop).filter(Shop.user_id == user_id, Shop.is_active == True).all()
        uzum_shop_ids = [shop.uzum_shop_id for shop in shops if shop.uzum_shop_id]
        if not uzum_shop_ids:
            return "Do'konlar yo'q."
        
        fbs_data = client.get_fbs_orders(shop_ids=uzum_shop_ids, size=50)
        sync_count = 0
        if fbs_data and 'orders' in fbs_data:
            for o in fbs_data['orders']:
                order_id = o.get("id") or o.get("orderId")
                status = o.get("status")
                shop_id = o.get("shopId")
                
                shop = db.query(Shop).filter(
                    Shop.user_id == user_id, Shop.uzum_shop_id == shop_id
                ).first()
                if shop:
                    fbs_order = db.query(FbsOrder).filter(
                        FbsOrder.user_id == user_id,
                        FbsOrder.uzum_order_id == order_id,
                    ).first()
                    if not fbs_order:
                        fbs_order = FbsOrder(user_id=user_id, shop_id=shop.id, uzum_order_id=order_id, status=status)
                        db.add(fbs_order)
                    else:
                        fbs_order.status = status
                    sync_count += 1
            db.commit()
        return f"{sync_count} ta FBS buyurtma sinxronlandi."
    finally:
        db.close()
