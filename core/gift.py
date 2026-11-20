# core/gift.py
"""سیستم کدهای گیفت محصولات"""

import random
import string
import time
from core.db_instance import db
from config import SHOP_PRODUCTS


def generate_gift_code(length=12) -> str:
    """تولید کد گیفت تصادفی (حروف بزرگ و اعداد)"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def create_gift(product_key: str, quantity: int = 1, expires_in_days: int = 30) -> dict:
    """
    ایجاد یک کد گیفت جدید

    Args:
        product_key: کلید محصول در SHOP_PRODUCTS
        quantity: تعداد محصول (برای محصولات عددی مثل پیشی یا پوینت)
        expires_in_days: تعداد روز اعتبار (پیش‌فرض ۳۰ روز)

    Returns:
        dict: اطلاعات کد گیفت
    """
    code = generate_gift_code()
    # جلوگیری از تکراری‌شدن
    while db.get_key(f"gift_{code}"):
        code = generate_gift_code()

    now = time.time()
    gift_data = {
        "code": code,
        "product_key": product_key,
        "quantity": quantity,
        "created_at": now,
        "expires_at": now + (expires_in_days * 86400),  # تبدیل روز به ثانیه
        "status": "available",  # available | used | expired
        "used_by": None,
        "used_at": None,
    }
    db.set_key(f"gift_{code}", gift_data)
    return gift_data


def get_gift_by_code(code: str) -> dict | None:
    """دریافت اطلاعات کد گیفت"""
    return db.get_key(f"gift_{code}")


def use_gift(code: str, user_id: str) -> tuple[bool, str]:
    """
    استفاده از کد گیفت توسط کاربر

    Args:
        code: کد گیفت
        user_id: شناسه کاربر

    Returns:
        tuple[bool, str]: (موفقیت, پیام)
    """
    gift = get_gift_by_code(code)
    if not gift:
        return False, "❌ کد گیفت معتبر نیست!"

    if gift["status"] == "used":
        return False, "❌ این کد قبلاً استفاده شده!"

    if gift["status"] == "expired":
        return False, "❌ اعتبار این کد به پایان رسیده!"

    # بررسی انقضا
    if time.time() > gift["expires_at"]:
        gift["status"] = "expired"
        db.set_key(f"gift_{code}", gift)
        return False, "❌ اعتبار این کد به پایان رسیده!"

    # تحویل محصول
    product_key = gift["product_key"]
    if product_key not in SHOP_PRODUCTS:
        return False, "❌ محصول نامعتبر!"

    user_data = db.get_key(user_id, {})
    product = SHOP_PRODUCTS[product_key]
    qty = gift.get("quantity", product["quantity"])

    # اعمال محصول به کاربر
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
        # افزایش سطح
        old_level = user_data.get("meow_level", 1)
        new_level = old_level + qty
        user_data["meow_level"] = new_level
        msg = f"✨ {qty} سطح بهت اضافه شد! سطح جدید: {new_level}"
    elif product_key == "special_role":
        from core.roles import set_user_role
        set_user_role(user_id, "special")
        msg = f"⭐ نقش ویژه بهت اعطا شد!"
    elif product_key == "premium_role":
        from core.roles import set_user_role
        set_user_role(user_id, "premium")
        msg = f"💎 نقش پریمیوم بهت اعطا شد!"
    elif product_key == "helper_role":
        from core.roles import set_user_role
        set_user_role(user_id, "helper")
        msg = f"🤝 نقش هلپر بهت اعطا شد!"
    else:
        msg = "✅ کد با موفقیت استفاده شد!"

    # به‌روزرسانی وضعیت گیفت
    gift["status"] = "used"
    gift["used_by"] = user_id
    gift["used_at"] = time.time()
    db.set_key(f"gift_{code}", gift)

    # ذخیره اطلاعات کاربر
    db.set_key(user_id, user_data)

    return True, msg


def get_all_gifts(status: str = None) -> list:
    """دریافت لیست همه کدهای گیفت (با فیلتر وضعیت)"""
    all_keys = db.get_all_keys()
    gifts = []
    for key in all_keys:
        if key.startswith("gift_"):
            gift = db.get_key(key, {})
            if status is None or gift.get("status") == status:
                gifts.append(gift)
    return gifts


def delete_gift(code: str) -> bool:
    """حذف کد گیفت (فقط برای ادمین)"""
    key = f"gift_{code}"
    if db.get_key(key):
        db.remove(key)
        return True
    return False