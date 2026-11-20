# handlers/street_market.py
"""هندلر مارکت میویی - خرید پیشی خیابونی، کرم ماهیگیری و افزایش سطح (نیازمند سطح شهر 7+)"""

from core.db_instance import db
from core.helpers import check_user_registered
from core.groups import get_user_group, get_city_level
from config import (
    MARKET_CITY_LEVEL_REQUIRED,
    MARKET_STREET_CAT_PRICE,
    MARKET_WORM_PRICE,
    LEVEL_ITEM_PRICE,
)
from core.street_market import get_daily_purchased, register_purchase
from core.gift import use_gift
from core.roles import get_user_role

ENTRY_KEYWORDS = ["مارکت میویی"]
BUY_CAT_PREFIX = "خرید پیشی "
BUY_WORM_PREFIX = "خرید کرم "
BUY_LEVEL_PREFIX = "خرید لول "
USE_WORM_KEYWORDS = ["استفاده از کرم", "استفاده کرم"]
GIFT_KEYWORDS = ["گیفت", "gift", "کد گیفت"]


def _get_daily_limit(user_id: str) -> int:
    """
    دریافت سقف خرید روزانه بر اساس نقش کاربر
    - نقش ویژه (special): ۱۵۰
    - نقش پریمیوم (premium): بدون محدودیت (عدد بسیار بزرگ)
    - سایر نقش‌ها: ۵۰
    """
    role = get_user_role(user_id)
    if role == "special":
        return 150
    elif role == "premium":
        return 999999  # عملاً بدون محدودیت
    else:
        return 50


def _get_remaining_daily(user_data: dict, user_id: str) -> int:
    """محاسبه تعداد باقی‌مانده سهمیه روزانه بر اساس نقش کاربر"""
    purchased = get_daily_purchased(user_data)  # تعداد خریداری‌شده امروز
    limit = _get_daily_limit(user_id)
    return max(0, limit - purchased)


def _get_city_level_for_user(sender_id, user_data):
    group_id = user_data.get('group_id') or get_user_group(sender_id)
    if not group_id:
        return None
    return get_city_level(group_id)


def _locked_message(city_level):
    if city_level is None:
        return (
            "🛍 مارکت میویی هنوز برای شما باز نشده!\n\n"
            "اول باید عضو یه سرزمین (گروه) بشی: توی یه گروه بگو «پیوستن به گروه»"
        )
    return (
        f"🛍 مارکت میویی هنوز باز نشده!\n\n"
        f"┘─ 🏰 سطح شهر لازم: {MARKET_CITY_LEVEL_REQUIRED}\n"
        f"┘─ 🏙 سطح فعلی شهر شما: {city_level}\n\n"
        f"با فعال‌ تر شدن سرزمینت (میو بیشتر اهالی)، سطح شهر بالا میره."
    )


def handle_market_entry(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in ENTRY_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    city_level = _get_city_level_for_user(sender_id, user_data)

    if city_level is None or city_level < MARKET_CITY_LEVEL_REQUIRED:
        bot.sendMessage(chat_id, _locked_message(city_level), reply_to_message_id=message_id)
        return True

    remaining = _get_remaining_daily(user_data, sender_id)
    limit = _get_daily_limit(sender_id)
    limit_display = "∞" if limit >= 999999 else f"{limit:,}"

    message = "🛍 مارکت میویی\n\n"
    message += f"🐈 پیشی خیابونی — {MARKET_STREET_CAT_PRICE:,} پوینت هر عدد\n"
    message += f"🎣 کرم ماهیگیری — {MARKET_WORM_PRICE:,} پوینت هر عدد\n"
    message += f"⭐️ افزایش سطح — {LEVEL_ITEM_PRICE:,} پوینت هر عدد\n\n"
    message += f"🧳 سهمیه امروز شما: {remaining:,} / {limit_display} باقی‌مونده\n\n"
    message += f"┘─ «{BUY_CAT_PREFIX}[تعداد]»\n"
    message += f"┘─ «{BUY_WORM_PREFIX}[تعداد]»\n"
    message += f"┘─ «{BUY_LEVEL_PREFIX}[تعداد]»\n"
    message += f"┘─ «استفاده از کرم» (رفع فوری کول‌داون ماهیگیری)"

    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True


def _handle_purchase(text, prefix, unit_price, item_label, apply_fn, sender_id, message_id, chat_id, bot):
    user_data = db.get_key(sender_id, {})
    city_level = _get_city_level_for_user(sender_id, user_data)

    if city_level is None or city_level < MARKET_CITY_LEVEL_REQUIRED:
        bot.sendMessage(chat_id, _locked_message(city_level), reply_to_message_id=message_id)
        return True

    raw = text[len(prefix):].strip()
    if not raw.isdigit() or int(raw) <= 0:
        bot.sendMessage(chat_id, f"❌ فرمت درست: «{prefix}[تعداد]»", reply_to_message_id=message_id)
        return True

    qty = int(raw)
    remaining = _get_remaining_daily(user_data, sender_id)
    limit = _get_daily_limit(sender_id)

    if remaining <= 0:
        bot.sendMessage(
            chat_id,
            "🧳 سهمیه خرید امروزت پر شده! تا ساعت 00:00 فردا صبر کن.",
            reply_to_message_id=message_id
        )
        return True

    if qty > remaining:
        bot.sendMessage(
            chat_id,
            f"❌ فقط {remaining:,} تا دیگه توی سهمیه امروزت جا داره!",
            reply_to_message_id=message_id
        )
        return True

    cost = qty * unit_price
    if user_data.get('meow_points', 0) < cost:
        bot.sendMessage(
            chat_id,
            f"❌ پوینت کافی نداری!\n💰 هزینه: {cost:,} پوینت\n📊 موجودی: {user_data.get('meow_points', 0):,} پوینت",
            reply_to_message_id=message_id
        )
        return True

    user_data['meow_points'] -= cost
    apply_fn(user_data, qty)
    register_purchase(user_data, qty)
    db.set_key(sender_id, user_data)

    remaining_after = _get_remaining_daily(user_data, sender_id)
    bot.sendMessage(
        chat_id,
        f"✅ {qty:,} عدد {item_label} خریداری شد!\n"
        f"💰 هزینه: {cost:,} پوینت\n"
        f"🧳 سهمیه باقی‌مانده امروز: {remaining_after:,} / {limit if limit < 999999 else '∞'}",
        reply_to_message_id=message_id
    )
    return True


def handle_buy_street_cat(text, sender_id, message_id, chat_id, bot) -> bool:
    if not text.startswith(BUY_CAT_PREFIX):
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    def apply(user_data, qty):
        user_data['rescued_cats_count'] = user_data.get('rescued_cats_count', 0) + qty

    return _handle_purchase(text, BUY_CAT_PREFIX, MARKET_STREET_CAT_PRICE, "پیشی خیابونی 🐈", apply, sender_id, message_id, chat_id, bot)


def handle_buy_worm(text, sender_id, message_id, chat_id, bot) -> bool:
    if not text.startswith(BUY_WORM_PREFIX):
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    def apply(user_data, qty):
        user_data['fishing_worms'] = user_data.get('fishing_worms', 0) + qty

    return _handle_purchase(text, BUY_WORM_PREFIX, MARKET_WORM_PRICE, "کرم ماهیگیری 🎣", apply, sender_id, message_id, chat_id, bot)


def handle_buy_level(text, sender_id, message_id, chat_id, bot) -> bool:
    """هندلر خرید آیتم افزایش سطح از مارکت"""
    if not text.startswith(BUY_LEVEL_PREFIX):
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    def apply(user_data, qty):
        user_data['meow_level'] = user_data.get('meow_level', 1) + qty

    return _handle_purchase(
        text,
        BUY_LEVEL_PREFIX,
        LEVEL_ITEM_PRICE,
        "افزایش سطح ⭐️",
        apply,
        sender_id,
        message_id,
        chat_id,
        bot
    )


def handle_use_worm(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in USE_WORM_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    worms = user_data.get('fishing_worms', 0)

    if worms <= 0:
        bot.sendMessage(
            chat_id,
            "❌ کرم ماهیگیری نداری! از «مارکت میویی» بخر.",
            reply_to_message_id=message_id
        )
        return True

    user_data['fishing_worms'] = worms - 1
    user_data['last_fishing'] = 0
    db.set_key(sender_id, user_data)

    bot.sendMessage(
        chat_id,
        f"🎣 یه کرم مصرف شد! کول‌داون ماهیگیریت رفع شد.\n"
        f"🧳 کرم‌ های باقی‌مانده: {user_data['fishing_worms']:,}\n\n"
        f"همین الان بگو «ماهیگیری»!",
        reply_to_message_id=message_id
    )
    return True


def handle_use_gift(text, sender_id, message_id, chat_id, bot) -> bool:
    """
    دستور: گیفت [کد]
    مثال: گیفت ABC123XYZ
    """
    if not text.lower().startswith("گیفت ") and not text.lower().startswith("gift "):
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        bot.sendMessage(
            chat_id,
            "❌ لطفاً کد گیفت را وارد کن!\nمثال: گیفت ABC123XYZ",
            reply_to_message_id=message_id
        )
        return True

    code = parts[1].strip().upper()
    if not code or len(code) < 6:
        bot.sendMessage(chat_id, "❌ کد وارد شده معتبر نیست!", reply_to_message_id=message_id)
        return True

    success, msg = use_gift(code, sender_id)
    bot.sendMessage(chat_id, msg, reply_to_message_id=message_id)
    return True