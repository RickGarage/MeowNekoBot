# handlers/admin_gift.py
"""کامندهای مدیریت کدهای گیفت (فقط ادمین)"""

from config import ADMIN_ID, SHOP_PRODUCTS
from core.db_instance import db
from core.gift import create_gift, get_all_gifts, delete_gift
from core.helpers import get_user_display_name


def handle_create_gift(text, sender_id, message_id, chat_id, bot) -> bool:
    """
    دستور ادمین: creategift [product_key] [تعداد] [روز اعتبار]
    مثال: creategift cat 10 30
    """
    if not text.lower().startswith("creategift "):
        return False

    if sender_id not in ADMIN_ID:
        bot.sendMessage(chat_id, "🚫 شما دسترسی به این کامند ندارید!", reply_to_message_id=message_id)
        return True

    parts = text.split()
    if len(parts) < 2:
        bot.sendMessage(
            chat_id,
            "❌ فرمت: creategift [product_key] [تعداد] [روز اعتبار]\n"
            "مثال: creategift cat 10 30\n"
            f"محصولات موجود: {', '.join(SHOP_PRODUCTS.keys())}",
            reply_to_message_id=message_id
        )
        return True

    product_key = parts[1].strip().lower()
    if product_key not in SHOP_PRODUCTS:
        bot.sendMessage(chat_id, f"❌ محصول '{product_key}' وجود ندارد!", reply_to_message_id=message_id)
        return True

    quantity = 1
    days = 30
    if len(parts) >= 3:
        try:
            quantity = int(parts[2])
        except ValueError:
            bot.sendMessage(chat_id, "❌ تعداد باید عدد باشد!", reply_to_message_id=message_id)
            return True
    if len(parts) >= 4:
        try:
            days = int(parts[3])
        except ValueError:
            bot.sendMessage(chat_id, "❌ روز اعتبار باید عدد باشد!", reply_to_message_id=message_id)
            return True

    gift = create_gift(product_key, quantity, days)
    product_name = SHOP_PRODUCTS[product_key]["name"]

    bot.sendMessage(
        chat_id,
        f"✅ کد گیفت ساخته شد!\n\n"
        f"🆔 کد: `{gift['code']}`\n"
        f"📦 محصول: {product_name}\n"
        f"🔢 تعداد: {quantity}\n"
        f"⏳ اعتبار: {days} روز\n\n"
        f"🔗 برای استفاده: کاربر باید «`گیفت {gift['code']}`» را وارد کند.",
        reply_to_message_id=message_id
    )
    return True


def handle_list_gifts(text, sender_id, message_id, chat_id, bot) -> bool:
    """
    دستور ادمین: listgifts [status]
    status: available, used, expired (اختیاری)
    """
    if not text.lower().startswith("listgifts"):
        return False

    if sender_id not in ADMIN_ID:
        bot.sendMessage(chat_id, "🚫 شما دسترسی به این کامند ندارید!", reply_to_message_id=message_id)
        return True

    parts = text.split()
    status = parts[1].strip().lower() if len(parts) > 1 else None
    if status and status not in ["available", "used", "expired"]:
        bot.sendMessage(chat_id, "❌ وضعیت معتبر: available, used, expired", reply_to_message_id=message_id)
        return True

    gifts = get_all_gifts(status)
    if not gifts:
        bot.sendMessage(chat_id, "📭 هیچ کد گیفتی با این وضعیت وجود ندارد.", reply_to_message_id=message_id)
        return True

    msg = f"📋 لیست کدهای گیفت ({'همه' if not status else status}):\n\n"
    for g in gifts[-20:]:  # حداکثر ۲۰ تا
        product_name = SHOP_PRODUCTS.get(g['product_key'], {}).get('name', g['product_key'])
        used_info = f" - استفاده شده توسط: {g.get('used_by', 'نامشخص')}" if g['status'] == 'used' else ""
        msg += f"┘─ `{g['code']}` | {product_name} | {g['status']}{used_info}\n"

    if len(gifts) > 20:
        msg += f"\n⚠️ فقط ۲۰ مورد آخر نمایش داده شد. (کل: {len(gifts)})"

    bot.sendMessage(chat_id, msg, reply_to_message_id=message_id)
    return True


def handle_delete_gift(text, sender_id, message_id, chat_id, bot) -> bool:
    """
    دستور ادمین: deletegift [code]
    """
    if not text.lower().startswith("deletegift "):
        return False

    if sender_id not in ADMIN_ID:
        bot.sendMessage(chat_id, "🚫 شما دسترسی به این کامند ندارید!", reply_to_message_id=message_id)
        return True

    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        bot.sendMessage(chat_id, "❌ کد گیفت را وارد کن! مثال: deletegift ABC123", reply_to_message_id=message_id)
        return True

    code = parts[1].strip().upper()
    if delete_gift(code):
        bot.sendMessage(chat_id, f"🗑️ کد گیفت `{code}` با موفقیت حذف شد.", reply_to_message_id=message_id)
    else:
        bot.sendMessage(chat_id, f"❌ کد گیفت `{code}` یافت نشد!", reply_to_message_id=message_id)
    return True