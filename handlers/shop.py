# handlers/shop.py
"""هندلر فروشگاه میویی - خرید با کد و اتصال به درگاه دارمت"""
import time
from core.db_instance import db
from core.helpers import check_user_registered, get_user_display_name
from core.shop import (
    purchase_with_wallet,
    create_order,
    get_order_by_code,
    create_wallet_order,
    SHOP_PRODUCTS
)
from config import SHOP_PRODUCTS,ADMIN_ID

SHOP_KEYWORDS = ["فروشگاه", "shop"]


def handle_shop_entry(text, sender_id, message_id, chat_id, bot) -> bool:
    """نمایش منوی فروشگاه"""
    if text.strip().lower() not in [kw.lower() for kw in SHOP_KEYWORDS]:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    msg = "🛒 **فروشگاه میویی**\n\n"
    msg += "با خرید از فروشگاه، از ربات حمایت مالی می‌کنی و پاداش می‌گیری! 😻\n\n"
    msg += "📦 **محصولات موجود:**\n"
    for key, product in SHOP_PRODUCTS.items():
        msg += f"┘─ {product['emoji']} **{product['name']}**\n"
        msg += f"   ┘─ قیمت: {product['price_toman']:,} تومان\n"
        msg += f"   ┘─ دریافت: {product['quantity']:,} عدد\n"
        msg += f"   ┘─ شناسه: `{key}`\n\n"
    msg += "🔹 نحوه خرید:\n"
    msg += "1️⃣ دستور زیر رو بفرست:\n"
    msg += "   `buy [شناسه محصول]`\n"
    msg += "2️⃣ ربات یه کد یکتا بهت میده (مثلاً `aB3dF7gH2jKl`).\n"
    msg += "3️⃣ روی لینک پرداخت کلیک کن، مبلغ رو وارد کن و در کادر **«پیام»** یا **«توضیحات»** (همون جایی که می‌تونی پیام بذاری) **دقیقاً همون کد** رو بنویس.\n"
    msg += "4️⃣ بعد از پرداخت، سیستم به‌صورت خودکار کد رو تشخیص میده و محصولات به حساب‌ت اضافه میشه! 🎉\n\n"
    msg += "📌 **نکات مهم:**\n"
    msg += "┘─ کد رو حتماً **انگلیسی** وارد کن و از کلمات رکیک بپرهیز.\n"
    msg += "┘─ کد رو در جای دیگه ننویس، فقط تو کادر پیام دارمت وارد کن.\n"
    msg += "┘─ اگر کد رو اشتباه وارد کنی، سفارش به‌صورت خودکار تحویل داده نمیشه و باید با پشتیبانی تماس بگیری."

    bot.sendMessage(chat_id, msg, reply_to_message_id=message_id)
    return True


def handle_shop_buy(text, sender_id, message_id, chat_id, bot) -> bool:
    """ایجاد سفارش جدید با کد"""
    if not text.lower().startswith("buy"):
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        bot.sendMessage(chat_id, "❌ لطفاً شناسه محصول رو وارد کن!", reply_to_message_id=message_id)
        return True

    product_key = parts[1].strip().lower()
    if product_key not in SHOP_PRODUCTS:
        bot.sendMessage(
            chat_id,
            f"❌ محصول با شناسه `{product_key}` وجود نداره!\n"
            f"محصولات موجود: {', '.join(SHOP_PRODUCTS.keys())}",
            reply_to_message_id=message_id
        )
        return True

    product = SHOP_PRODUCTS[product_key]
    order = create_order(sender_id, product_key, product["price_toman"])
    code = order["code"]

    payment_link = f"https://daramet.com/meow_neko"

    msg = (
        f"🧾 سفارش شما ثبت شد!(کاربر: {get_user_display_name(bot,sender_id)})\n\n"
        f"┘─ 🆔 کد خرید: `{code}`\n"
        f"┘─ 🛍 محصول: {product['emoji']} {product['name']}\n"
        f"┘─ 💰 مبلغ: {product['price_toman']:,} تومان\n\n"
        f"🔗 لینک پرداخت:\n{payment_link}\n\n"
        f"⚠️ بعد از پرداخت، کد رو به ربات **ندید**، سیستم خودکار انجام میشه.\n"
        f"اگر پرداخت انجام نشد، دوباره سفارش جدید ثبت کن."
    )
    bot.sendMessage(chat_id, msg, reply_to_message_id=message_id)
    return True


def handle_shop_check(text, sender_id, message_id, chat_id, bot) -> bool:
    if not text.lower().startswith("بررسی سفارش "):
        return False

    parts = text.split(maxsplit=2)
    if len(parts) < 3:
        bot.sendMessage(chat_id, "❌ کد سفارش رو وارد کن!", reply_to_message_id=message_id)
        return True

    code = parts[2].strip()
    order = get_order_by_code(code)
    if not order:
        bot.sendMessage(chat_id, "❌ سفارشی با این کد پیدا نشد.", reply_to_message_id=message_id)
        return True

    if order["user_id"] != sender_id:
        bot.sendMessage(chat_id, "❌ این سفارش متعلق به شما نیست!", reply_to_message_id=message_id)
        return True

    status = order["status"]
    status_map = {
        "pending": "⏳ در انتظار پرداخت",
        "paid": "✅ پرداخت شده (در حال تحویل)",
        "delivered": "🎉 تحویل داده شده",
        "partial": "⚠️ پرداخت ناقص"
    }
    msg = f"📋 وضعیت سفارش(کاربر: {get_user_display_name(bot,sender_id)}):\n"
    msg += f"┘─ کد: `{code}`\n"
    msg += f"┘─ وضعیت: {status_map.get(status, status)}\n"
    if order.get("paid_at"):
        msg += f"┘─ زمان پرداخت: {time.strftime('%Y-%m-%d %H:%M', time.localtime(order['paid_at']))}\n"
    if order.get("paid_amount"):
        msg += f"┘─ مبلغ پرداختی: {order['paid_amount']:,} تومان\n"
    bot.sendMessage(chat_id, msg, reply_to_message_id=message_id)
    return True


def handle_shop_buy_with_wallet(text, sender_id, message_id, chat_id, bot) -> bool:
    if not text.lower().startswith("خرید با کیف پول "):
        return False
    if not check_user_registered(sender_id, chat_id, bot):
        return True

    parts = text.split(maxsplit=3)
    if len(parts) < 4:
        bot.sendMessage(chat_id, "❌ شناسه محصول رو وارد کن!", reply_to_message_id=message_id)
        return True

    product_key = parts[3].strip().lower()
    if product_key not in SHOP_PRODUCTS:
        bot.sendMessage(chat_id, f"❌ محصول `{product_key}` وجود نداره!", reply_to_message_id=message_id)
        return True

    success, msg = purchase_with_wallet(sender_id, product_key)
    if success:
        bot.sendMessage(chat_id, f"✅ خرید موفق!\n\n{msg}", reply_to_message_id=message_id)
    else:
        bot.sendMessage(chat_id, f"❌ {msg}", reply_to_message_id=message_id)
    return True


def handle_wallet_charge(text, sender_id, message_id, chat_id, bot) -> bool:
    if not text.lower().startswith("شارژ کیف پول "):
        return False
    if not check_user_registered(sender_id, chat_id, bot):
        return True

    parts = text.split()
    if len(parts) < 3:
        bot.sendMessage(chat_id, "❌ مبلغ رو به تومان وارد کن!", reply_to_message_id=message_id)
        return True

    try:
        amount = int(parts[3])
    except ValueError:
        bot.sendMessage(chat_id, "❌ مبلغ باید عدد باشه!", reply_to_message_id=message_id)
        return True

    if amount <= 0:
        bot.sendMessage(chat_id, "❌ مبلغ باید بزرگتر از صفر باشه!", reply_to_message_id=message_id)
        return True

    order = create_wallet_order(sender_id, amount)
    code = order["code"]
    payment_link = f"https://daramet.com/meow_neko"

    msg = (
        f"🧾 **درخواست شارژ کیف پول ثبت شد!**\n\n"
        f"┘─ 🆔 کد: `{code}`\n"
        f"┘─ 💰 مبلغ: {amount:,} تومان\n\n"
        f"🔗 **لینک پرداخت:**\n{payment_link}\n\n"
        f"⚠️ پس از پرداخت، موجودی کیف پول شما به‌صورت خودکار افزایش می‌یابد.\n"
        f"📌 کد رو در کادر **«پیام»** دارمت وارد کن."
    )
    bot.sendMessage(chat_id, msg, reply_to_message_id=message_id)
    return True


def handle_wallet_balance(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip().lower() not in ["موجودی کیف پول", "کیف پول", "wallet"]:
        return False
    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    wallet = user_data.get("wallet_balance", 0)
    bot.sendMessage(chat_id, f"💰 موجودی کیف پول شما: {wallet:,} تومان", reply_to_message_id=message_id)
    return True


def handle_shop_check(text, sender_id, message_id, chat_id, bot) -> bool:
    if not text.lower().startswith("بررسی سفارش "):
        return False
    if not check_user_registered(sender_id, chat_id, bot):
        return True

    parts = text.split(maxsplit=2)
    if len(parts) < 3:
        bot.sendMessage(chat_id, "❌ کد سفارش رو وارد کن!", reply_to_message_id=message_id)
        return True

    code = parts[2].strip()
    from core.shop import get_order_by_code
    order = get_order_by_code(code)
    if not order:
        bot.sendMessage(chat_id, "❌ سفارشی با این کد پیدا نشد.", reply_to_message_id=message_id)
        return True
    if not sender_id in ADMIN_ID:
        if order["user_id"] != sender_id:
            bot.sendMessage(chat_id, "❌ این سفارش متعلق به شما نیست!", reply_to_message_id=message_id)
            return True

    status = order["status"]
    status_map = {
        "pending": "⏳ در انتظار پرداخت",
        "paid": "✅ پرداخت شده (در حال تحویل)",
        "delivered": "🎉 تحویل داده شده",
        "partial": "⚠️ پرداخت ناقص"
    }
    msg = f"📋 **وضعیت سفارش:**\n"
    msg += f"┘─ کد: `{code}`\n"
    msg += f"┘─ وضعیت: {status_map.get(status, status)}\n"
    if order.get("paid_at"):
        msg += f"┘─ زمان پرداخت: {time.strftime('%Y-%m-%d %H:%M', time.localtime(order['paid_at']))}\n"
    if order.get("paid_amount"):
        msg += f"┘─ مبلغ پرداختی: {order['paid_amount']:,} تومان\n"
    bot.sendMessage(chat_id, msg, reply_to_message_id=message_id)
    return True