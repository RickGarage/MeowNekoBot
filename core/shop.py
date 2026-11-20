# core/shop.py
"""مدیریت فروشگاه و کدهای خرید"""

import re
import time
import random
import string
from core.db_instance import db
from config import FORBIDDEN_CODE_WORDS, SHOP_PRODUCTS
from core.roles import get_role_display_name


def generate_shop_code(length=12) -> str:
    chars = string.ascii_letters + string.digits
    code = ''.join(random.choice(chars) for _ in range(length))
    return code


def is_code_valid(code: str) -> bool:
    if not re.match(r'^[A-Za-z0-9]{6,}$', code):
        return False
    lower_code = code.lower()
    for bad in FORBIDDEN_CODE_WORDS:
        if bad in lower_code:
            return False
    return True


def create_order(user_id: str, product_key: str, amount_toman: int) -> dict:
    code = generate_shop_code()
    while db.get_key(f"shop_order_{code}"):
        code = generate_shop_code()
    order_data = {
        "user_id": user_id,
        "product_key": product_key,
        "amount_toman": amount_toman,
        "code": code,
        "status": "pending",
        "type": "product",
        "created_at": time.time(),
        "paid_at": None,
        "delivered_at": None,
    }
    db.set_key(f"shop_order_{code}", order_data)
    return order_data


def create_wallet_order(user_id: str, amount_toman: int) -> dict:
    code = generate_shop_code()
    while db.get_key(f"shop_order_{code}"):
        code = generate_shop_code()
    order_data = {
        "user_id": user_id,
        "amount_toman": amount_toman,
        "code": code,
        "status": "pending",
        "type": "wallet",
        "created_at": time.time(),
        "paid_at": None,
        "delivered_at": None,
    }
    db.set_key(f"shop_order_{code}", order_data)
    return order_data


def get_order_by_code(code: str) -> dict | None:
    return db.get_key(f"shop_order_{code}")


def update_order_status(code: str, status: str, paid_amount: int = None) -> bool:
    order = get_order_by_code(code)
    if not order:
        return False
    order["status"] = status
    if status in ("paid", "delivered", "partial"):
        order["paid_at"] = time.time()
        if paid_amount is not None:
            order["paid_amount"] = paid_amount
    if status == "delivered":
        order["delivered_at"] = time.time()
    db.set_key(f"shop_order_{code}", order)
    return True


def deliver_order_products(order: dict, user_id: str) -> str:
    product_key = order["product_key"]
    product = SHOP_PRODUCTS[product_key]
    qty = product["quantity"]
    user_data = db.get_key(user_id, {})
    
    if product_key == "cat":
        user_data["rescued_cats_count"] = user_data.get("rescued_cats_count", 0) + qty
        msg = f"🐈 {qty} عدد پیشی خیابونی بهت اضافه شد!"
    elif product_key == "meow":
        user_data["meow_count"] = user_data.get("meow_count", 0) + qty
        msg = f"💰 {qty} تا میو پوینت بهت اضافه شد!"
    elif product_key == "point":
        user_data["meow_points"] = user_data.get("meow_points", 0) + qty
        msg = f"💎 {qty:,} میو پوینت بهت اضافه شد!"
    else:
        msg = "❌ محصول نامشخص!"
    
    db.set_key(user_id, user_data)
    return msg


# core/shop.py (بخش‌های اصلاح‌شده)

def deliver_order_products(order: dict, user_id: str) -> str:
    product_key = order["product_key"]
    product = SHOP_PRODUCTS[product_key]
    qty = product["quantity"]
    user_data = db.get_key(user_id, {})
    
    if product_key == "cat":
        user_data["rescued_cats_count"] = user_data.get("rescued_cats_count", 0) + qty
        msg = f"🐈 {qty} عدد پیشی خیابونی بهت اضافه شد!"
    elif product_key == "meow":
        user_data["meow_count"] = user_data.get("meow_count", 0) + qty
        msg = f"💰 {qty} تا میو پوینت بهت اضافه شد!"
    elif product_key == "point":
        user_data["meow_points"] = user_data.get("meow_points", 0) + qty
        msg = f"💎 {qty:,} میو پوینت بهت اضافه شد!"
    elif product_key == "level":
        user_data["meow_level"] = user_data.get("meow_level", 1) + qty
        msg = f"✨ {qty} لول بهت اضافه شد! سطح جدید: {user_data['meow_level']}"
    elif product_key == "special_role" or product_key == "premium_role":
        role = product.get("role")
        if role:
            from core.roles import set_user_role
            set_user_role(user_id, role)
            role_display = get_role_display_name(role)
            msg = f"🎉 نقش {role_display} به شما اعطا شد!"
        else:
            msg = "❌ نقش نامشخص!"
    else:
        msg = "❌ محصول نامشخص!"
    
    db.set_key(user_id, user_data)
    return msg


def deliver_order_products_direct(user_id: str, product_key: str) -> str:
    product = SHOP_PRODUCTS[product_key]
    qty = product["quantity"]
    user_data = db.get_key(user_id, {})
    
    if product_key == "cat":
        user_data["rescued_cats_count"] = user_data.get("rescued_cats_count", 0) + qty
        msg = f"🐈 {qty} عدد پیشی خیابونی بهت اضافه شد!"
    elif product_key == "meow":
        user_data["meow_count"] = user_data.get("meow_count", 0) + qty
        msg = f"💰 {qty} تا میو پوینت بهت اضافه شد!"
    elif product_key == "point":
        user_data["meow_points"] = user_data.get("meow_points", 0) + qty
        msg = f"💎 {qty:,} میو پوینت بهت اضافه شد!"
    elif product_key == "level":
        user_data["meow_level"] = user_data.get("meow_level", 1) + qty
        msg = f"✨ {qty} لول بهت اضافه شد! سطح جدید: {user_data['meow_level']}"
    elif product_key == "special_role" or product_key == "premium_role":
        role = product.get("role")
        if role:
            from core.roles import set_user_role
            set_user_role(user_id, role)
            role_display = get_role_display_name(role)
            msg = f"🎉 نقش {role_display} به شما اعطا شد!"
        else:
            msg = "❌ نقش نامشخص!"
    else:
        msg = "❌ محصول نامشخص!"
    
    db.set_key(user_id, user_data)
    return msg

def purchase_with_wallet(user_id: str, product_key: str) -> tuple[bool, str]:
    if product_key not in SHOP_PRODUCTS:
        return False, "محصول نامعتبر"
    
    user_data = db.get_key(user_id, {})
    wallet = user_data.get("wallet_balance", 0)
    product = SHOP_PRODUCTS[product_key]
    price = product["price_toman"]
    
    if wallet < price:
        return False, f"موجودی کیف پول کافی نیست! نیاز: {price:,} تومان، موجودی: {wallet:,} تومان"
    
    user_data["wallet_balance"] = wallet - price
    db.set_key(user_id, user_data)
    
    deliver_msg = deliver_order_products_direct(user_id, product_key)
    return True, deliver_msg