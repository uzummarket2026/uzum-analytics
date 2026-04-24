from app.db.session import SessionLocal
from app.db.models import Product, Order, Shop, Expense, Invoice, FbsOrder, Return, ReturnItem, InvoiceItem, SystemSetting
from app.core.config import settings
from app.services.uzum_client import UzumClient, UzumForbiddenError
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_api_token(db) -> str:
    setting = db.query(SystemSetting).filter(SystemSetting.key == "uzum_api_token").first()
    if setting and setting.value:
        return setting.value
    return settings.UZUM_API_TOKEN

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
    log_path = r"c:\Users\user\Desktop\uzum Pyton\backend\image_debug.txt"
    try:
        with open(log_path, "a") as f:
            f.write(f"CALL with: {url_data}\n")
    except:
        pass

    if not url_data:
        return None
        
    if isinstance(url_data, dict):
        url_data = url_data.get("high") or url_data.get("low") or url_data.get("photoKey") or url_data.get("url")
    
    if isinstance(url_data, str):
        url_data = url_data.strip()
        if not url_data: return None
        
        res = url_data
        if url_data.startswith("https://") or url_data.startswith("http://"):
            res = url_data
        elif url_data.startswith("//"):
            res = f"https:{url_data}"
        elif "/" not in url_data:
            res = f"https://images.uzum.uz/{url_data}/t_product_540_high.jpg"
            return res # Allaqachon suffix qo'shildi
        elif url_data.startswith("/"):
            res = f"https://images.uzum.uz{url_data}"
        else:
            res = f"https://images.uzum.uz/{url_data}"
        
        # Muhim: Agar URL'da nuqta bo'lmasa (ya'ni kengaytma yo'q bo'lsa)
        # yoki u /t_product bilan tugamasa, suffix qo'shamiz
        if "images.uzum.uz" in res and not any(ext in res.lower() for ext in [".jpg", ".png", ".jpeg", ".webp"]):
            if not res.endswith("/"):
                res += "/"
            res += "t_product_540_high.jpg"
            
        try:
            with open(log_path, "a") as f:
                f.write(f"FINAL: {res}\n")
        except:
            pass
        return res
            
    return str(url_data) if url_data else None

def sync_uzum_data_task() -> str:
    db = SessionLocal()
    try:
        log_file = "c:/Users/user/Desktop/uzum Pyton/scratch/sync_log.txt"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n--- Sinxronizatsiya boshlandi: {datetime.now()} ---\n")
        except:
            pass
        
        token = get_api_token(db)
        if not token:
            logger.error("XATO: Uzum API token topilmadi!")
            return "Token topilmadi"
        
        client = UzumClient(token)
        
        # 1. Sync Shops
        try:
            shops_data = client.get_shops()
            logger.info(f"API dan kelgan do'konlar soni: {len(shops_data) if shops_data else 0}")
            
            if not shops_data:
                logger.warning("OGOHLANTIRISH: Do'konlar ro'yxati bo'sh keldi.")
            
            # Reset is_active for all shops before syncing
            db.query(Shop).update({Shop.is_active: False})
            
            for shop_info in shops_data:
                shop_id = shop_info.get("id")
                name = shop_info.get("name", "Unknown Shop")
                logger.info(f"Do'kon saqlanmoqda: {name} (ID: {shop_id})")
                
                shop = db.query(Shop).filter(Shop.uzum_shop_id == shop_id).first()
                if not shop:
                    shop = Shop(uzum_shop_id=shop_id, name=name, is_active=True)
                    db.add(shop)
                else:
                    shop.name = name
                    shop.is_active = True
            db.commit()
        except Exception as e:
            logger.error(f"Do'konlarni sinxronlashda xato: {e}")
        
        product_sync_count = 0
        db_shops = db.query(Shop).filter(Shop.is_active == True).all()
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
                        product_main_image = safe_url(
                            p_card.get("image") or 
                            p_card.get("previewImg") or 
                            p_card.get("previewImage") or 
                            p_card.get("photoKey") or
                            p_card.get("photo")
                        )
                        
                        sku_items = p_card.get('skuList', [])
                        for sku_data in sku_items:
                            sku_id = sku_data.get("skuId")
                            if not sku_id: continue
                            
                            sku_title = sku_data.get("skuFullTitle") or sku_data.get("skuTitle") or product_title
                            sku_code = sku_data.get("article") or sku_data.get("sellerItemCode") or str(sku_id)
                            sku_image = safe_url(
                                sku_data.get("previewImage") or 
                                sku_data.get("previewImg") or
                                sku_data.get("image") or
                                sku_data.get("photoKey")
                            ) or product_main_image
                            
                            price = sku_data.get("price")
                            purchase_price = sku_data.get("purchasePrice")
                            commission_percent = sku_data.get("commission")
                            
                            fbo_stock = safe_int(sku_data.get("quantityActive"), 0)
                            fbs_stock = safe_int(sku_data.get("quantityFbs"), 0)
                            stock = fbo_stock + fbs_stock
                            
                            product = db.query(Product).filter(Product.sku_id == sku_id).first()
                            if product:
                                product.stock = stock
                                product.fbo_stock = fbo_stock
                                product.fbs_stock = fbs_stock
                                product.price = safe_float(price)
                                product.purchase_price = safe_float(purchase_price)
                                product.commission_percent = safe_float(commission_percent)
                                product.title = sku_title
                                product.sku_code = sku_code
                                product.uzum_product_id = uzum_product_id
                                product.shop_id = shop.id
                                product.image_url = sku_image
                            else:
                                product = Product(
                                    shop_id=shop.id,
                                    uzum_product_id=uzum_product_id,
                                    sku_id=sku_id,
                                    sku_code=sku_code,
                                    title=sku_title,
                                    price=safe_float(price),
                                    purchase_price=safe_float(purchase_price),
                                    commission_percent=safe_float(commission_percent),
                                    stock=stock,
                                    fbo_stock=fbo_stock,
                                    fbs_stock=fbs_stock,
                                    image_url=sku_image
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

def backfill_product_purchase_prices(db=None) -> str:
    """
    Tannarxlarni /v1/shop/{shopId}/invoice/products API dan olib Product ga yozadi.
    Har bir SKU uchun eng so'nggi invoice'dagi tannarx ustunlik oladi.
    Swagger: ProductForInvoiceDto.skuForInvoiceDtoList[].purchasePrice
    """
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        token = get_api_token(db)
        client = UzumClient(api_token=token)
        shops = db.query(Shop).filter(Shop.is_active == True).all()

        updated = 0
        invoices_scanned = 0
        checked_skus = set()  # bir SKU uchun faqat eng yangi invoice'dan olamiz

        for shop in shops:
            try:
                all_invoices = []
                page = 0
                while page < 20:
                    time.sleep(0.1)
                    inv_list = client.get_invoices(shop_id=shop.uzum_shop_id, page=page, size=50)
                    if not inv_list or not isinstance(inv_list, list):
                        break
                    all_invoices.extend(inv_list)
                    if len(inv_list) < 50:
                        break
                    page += 1

                # dateCreated DESC bo'yicha saralash (yangiroqlar oldin) — ID fallback
                all_invoices.sort(key=lambda i: str(i.get("dateAccepted") or i.get("dateCreated") or i.get("id") or 0), reverse=True)

                for inv in all_invoices:
                    inv_id = inv.get("id")
                    if not inv_id:
                        continue

                    time.sleep(0.1)
                    products = client.get_invoice_products(shop.uzum_shop_id, inv_id)
                    if not products or not isinstance(products, list):
                        continue
                    invoices_scanned += 1

                    for prod in products:
                        prod_level_pp = safe_float(prod.get("purchasePrice"), 0)
                        sku_items = prod.get("skuForInvoiceDtoList") or []

                        for sku in sku_items:
                            sku_id = sku.get("id")
                            if not sku_id or sku_id in checked_skus:
                                continue

                            pp = safe_float(sku.get("purchasePrice"), 0)
                            if pp <= 0:
                                pp = prod_level_pp
                            if pp <= 0:
                                continue

                            checked_skus.add(sku_id)
                            product = db.query(Product).filter(Product.sku_id == sku_id).first()
                            if product and product.purchase_price != pp:
                                product.purchase_price = pp
                                updated += 1
            except UzumForbiddenError:
                continue
            except Exception as e:
                logger.error(f"Backfill for shop {shop.id}: {e}")
                db.rollback()

        db.commit()
        return f"Invoice API'dan {updated} ta mahsulotga tannarx yozildi ({invoices_scanned} ta yukxat tekshirildi, {len(checked_skus)} noyob SKU)"
    finally:
        if own_session:
            db.close()


def sync_uzum_orders_task() -> str:
    db = SessionLocal()
    try:
        token = get_api_token(db)
        client = UzumClient(api_token=token)
        shops = db.query(Shop).filter(Shop.is_active == True).all()
        if not shops: return "Do'konlar yo'q."
        
        # Uzum Shop ID -> local Shop ID xaritasi
        shop_map = {shop.uzum_shop_id: shop.id for shop in shops}
        all_uzum_shop_ids = list(shop_map.keys())
            
        sync_count = 0
        date_from = int((time.time() - 30 * 24 * 60 * 60) * 1000) # Swagger: date in milliseconds
        
        # Barcha do'konlar uchun birgalikda so'rov yuborish
        try:
            page = 0
            while page < 1000:
                time.sleep(0.1)
                orders_data = client.get_orders(shop_ids=all_uzum_shop_ids, date_from=date_from, page=page, size=100)
                
                if not orders_data or 'orderItems' not in orders_data or not orders_data['orderItems']:
                    break

                for o_data in orders_data['orderItems']:
                    # Swagger: id (orderItem ID), orderId, shopId, amount, sellerPrice, purchasePrice, commission, logisticDeliveryFee, sellerProfit
                    uzum_item_id = o_data.get('id')
                    uzum_order_id = o_data.get('orderId')
                    uzum_product_id = o_data.get('productId')
                    uzum_shop_id_val = o_data.get('shopId')
                    local_shop_id = shop_map.get(uzum_shop_id_val)
                    status = o_data.get('status', 'PENDING')
                    quantity = safe_int(o_data.get('amount'), 1)
                    amount_returns = safe_int(o_data.get('amountReturns'), 0)
                    cancelled = safe_int(o_data.get('cancelled'), 0)
                    price = safe_float(o_data.get('sellerPrice'), 0)
                    purchase_price = safe_float(o_data.get('purchasePrice'), 0)
                    commission_amount = safe_float(o_data.get('commission'), 0)
                    logistic_fee = safe_float(o_data.get('logisticDeliveryFee'), 0)
                    seller_profit = safe_float(o_data.get('sellerProfit'), 0)
                    withdrawn_profit = safe_float(o_data.get('withdrawnProfit'), 0)
                    
                    sku_title = o_data.get('skuTitle')
                    sku_char_title = o_data.get('skuCharTitle')
                    sku_char_value = o_data.get('skuCharValue')
                    
                    product = db.query(Product).filter(
                        Product.uzum_product_id == uzum_product_id,
                        Product.title == sku_title
                    ).first()
                    
                    sku_code = product.sku_code if product else None

                    order = db.query(Order).filter(Order.uzum_order_id == uzum_item_id).first()
                    order_timestamp = o_data.get('date') # Unix Epoch ms
                    order_date = None
                    if order_timestamp:
                        from datetime import datetime
                        order_date = datetime.fromtimestamp(order_timestamp / 1000.0)

                    net_quantity = max(quantity - amount_returns, 0)
                    total_price_val = float(price * net_quantity)

                    if not order:
                        order = Order(
                            uzum_order_id=uzum_item_id,
                            main_order_id=uzum_order_id,
                            shop_id=local_shop_id,
                            uzum_shop_id=uzum_shop_id_val,
                            product_id=product.id if product else None,
                            quantity=quantity,
                            amount_returns=amount_returns,
                            cancelled=cancelled,
                            total_price=total_price_val,
                            purchase_price=purchase_price,
                            commission_amount=commission_amount,
                            logistic_fee=logistic_fee,
                            seller_profit=seller_profit,
                            withdrawn_profit=withdrawn_profit,
                            sku_code=sku_code,
                            sku_title=sku_title,
                            sku_char_title=sku_char_title,
                            sku_char_value=sku_char_value,
                            status=status.lower(),
                            order_date=order_date,
                        )
                        db.add(order)
                        sync_count += 1
                    else:
                        order.status = status.lower()
                        order.main_order_id = uzum_order_id
                        order.shop_id = local_shop_id
                        order.uzum_shop_id = uzum_shop_id_val
                        order.quantity = quantity
                        order.amount_returns = amount_returns
                        order.cancelled = cancelled
                        order.total_price = total_price_val
                        order.purchase_price = purchase_price
                        order.commission_amount = commission_amount
                        order.logistic_fee = logistic_fee
                        order.seller_profit = seller_profit
                        order.withdrawn_profit = withdrawn_profit
                        order.sku_code = sku_code
                        order.sku_title = sku_title
                        order.sku_char_title = sku_char_title
                        order.sku_char_value = sku_char_value
                        if order_date:
                            order.order_date = order_date
                
                if len(orders_data['orderItems']) < 100:
                    break
                page += 1
                
            db.commit()
        except Exception as e:
            logger.error(f"Order sync error: {e}")
            db.rollback()

        return f"{sync_count} ta buyurtma sinxronlandi."
    finally:
        db.close()

def sync_expenses_task() -> str:
    db = SessionLocal()
    try:
        token = get_api_token(db)
        client = UzumClient(api_token=token)
        shops = db.query(Shop).filter(Shop.is_active == True).all()
        uzum_shop_ids = [shop.uzum_shop_id for shop in shops if shop.uzum_shop_id]
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

                shop = db.query(Shop).filter(Shop.uzum_shop_id == shop_id).first()
                if not shop:
                    continue

                expense = db.query(Expense).filter(Expense.uzum_payment_id == payment_id).first()
                if expense:
                    expense.amount = amount
                    expense.name = name
                    expense.source = source
                    expense.date = date_val
                    expense.payment_type = payment_type
                    expense.status = status
                else:
                    expense = Expense(
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

def sync_invoices_task() -> str:
    db = SessionLocal()
    try:
        token = get_api_token(db)
        client = UzumClient(api_token=token)
        shops = db.query(Shop).filter(Shop.is_active == True).all()
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

                        db_inv = db.query(Invoice).filter(Invoice.uzum_invoice_id == inv_id).first()
                        if not db_inv:
                            db_inv = Invoice(shop_id=shop.id, uzum_invoice_id=inv_id, status=status, invoice_type="supply")
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
        backfill_msg = backfill_product_purchase_prices(db)
        return f"{sync_count} ta yukxat sinxronlandi. {backfill_msg}"
    finally:
        db.close()

def sync_returns_task() -> str:
    db = SessionLocal()
    try:
        token = get_api_token(db)
        client = UzumClient(api_token=token)
        shops = db.query(Shop).filter(Shop.is_active == True).all()
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
                    
                    db_ret = db.query(Return).filter(Return.uzum_return_id == ret_id).first()
                    if not db_ret:
                        db_ret = Return(shop_id=shop.id, uzum_return_id=ret_id, status=status)
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

def sync_fbs_orders_task() -> str:
    db = SessionLocal()
    try:
        token = get_api_token(db)
        client = UzumClient(api_token=token)
        shops = db.query(Shop).filter(Shop.is_active == True).all()
        uzum_shop_ids = [shop.uzum_shop_id for shop in shops if shop.uzum_shop_id]
        if not uzum_shop_ids: return "Do'konlar yo'q."
        
        fbs_data = client.get_fbs_orders(shop_ids=uzum_shop_ids, size=50)
        sync_count = 0
        if fbs_data and 'orders' in fbs_data:
            for o in fbs_data['orders']:
                order_id = o.get("id") or o.get("orderId")
                status = o.get("status")
                shop_id = o.get("shopId")
                
                shop = db.query(Shop).filter(Shop.uzum_shop_id == shop_id).first()
                if shop:
                    fbs_order = db.query(FbsOrder).filter(FbsOrder.uzum_order_id == order_id).first()
                    if not fbs_order:
                        fbs_order = FbsOrder(shop_id=shop.id, uzum_order_id=order_id, status=status)
                        db.add(fbs_order)
                    else:
                        fbs_order.status = status
                    sync_count += 1
            db.commit()
        return f"{sync_count} ta FBS buyurtma sinxronlandi."
    finally:
        db.close()
