# handlers/factory.py
"""هندلر کارخونه میویی - ساخت، کارگران، تولید، ارتقا انبار/دستگاه، فروش در بازار"""

import time

from core.db_instance import db
from core.helpers import check_user_registered, format_time
from core.conversations import start_conversation, get_conversation, update_conversation, clear_conversation
from config import FACTORY_MIN_LEVEL, FACTORY_BUILD_COST, FACTORY_PRODUCTS
from core.factory import (
    has_factory,
    create_factory,
    warehouse_capacity,
    warehouse_upgrade_cost,
    cycle_seconds,
    machine_upgrade_cost,
    total_stored,
    level_up_threshold,
    get_unlocked_products,
    available_workers_to_hire,
    hire_workers,
    fire_workers,
    sync_production,
)
from core.market import get_product_price, get_all_prices, get_price_trend_label

ENTRY_KEYWORDS = ["کارخونه میویی", "کارخونه من"]
HIRE_PREFIX = "استخدام کارگر "
FIRE_PREFIX = "اخراج کارگر "
START_PRODUCTION_KEYWORDS = ["شروع تولید", "تولید کارخونه"]
UPGRADE_WAREHOUSE_KEYWORDS = ["ارتقا انبار"]
UPGRADE_MACHINE_KEYWORDS = ["ارتقا دستگاه"]
SELL_START_KEYWORDS = ["فروش کارخونه"]
MARKET_VIEW_KEYWORDS = ["بازار کارخونه", "قیمت بازار"]
CANCEL_KEYWORDS = ["لغو", "cancel", "انصراف"]

CONV_PRODUCTION = "factory_production"
CONV_SELL = "factory_sell"


def _no_factory_message(user_level):
    return (
        f"🏭 هنوز کارخونه‌ای نداری!\n\n"
        f"┘─ ⭐️ حداقل سطح لازم: {FACTORY_MIN_LEVEL} (سطح فعلی شما: {user_level})\n"
        f"┘─ 💰 هزینه ساخت: {FACTORY_BUILD_COST:,} پوینت\n\n"
        f"برای ساخت دوباره بگو «کارخونه میویی» 🏭"
    )


def _sync_and_get(user_data):
    factory = user_data['factory']
    result = sync_production(factory)
    return factory, result


def _production_notice(result):
    if result['produced'] <= 0:
        return ""
    product_name = FACTORY_PRODUCTS[result['product_id']]['name']
    msg = f"\n📦 در این مدت {result['produced']:,} عدد {product_name} تولید شد!"
    if result['leveled_up_to']:
        msg += f"\n🎉 کارخونه به سطح {result['leveled_up_to']} ارتقا پیدا کرد!"
    return msg


# ============================================================
# ساخت / وضعیت
# ============================================================

def handle_factory_entry(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in ENTRY_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})

    if not has_factory(user_data):
        user_level = user_data.get('meow_level', 1)
        user_points = user_data.get('meow_points', 0)

        if user_level < FACTORY_MIN_LEVEL:
            bot.sendMessage(chat_id, _no_factory_message(user_level), reply_to_message_id=message_id)
            return True

        if user_points < FACTORY_BUILD_COST:
            bot.sendMessage(
                chat_id,
                f"❌ پوینت کافی برای ساخت کارخونه نداری!\n"
                f"💰 هزینه: {FACTORY_BUILD_COST:,} پوینت\n📊 موجودی: {user_points:,} پوینت",
                reply_to_message_id=message_id
            )
            return True

        user_data['meow_points'] = user_points - FACTORY_BUILD_COST
        user_data['factory'] = create_factory()
        db.set_key(sender_id, user_data)

        bot.sendMessage(
            chat_id,
            f"🎉 کارخونه میویی‌ ات ساخته شد! 🏭\n\n"
            f"🐈 حالا باید کارگر استخدام کنی: «استخدام کارگر [تعداد]»\n"
            f"🏭 بعدش تولید رو شروع کن: «شروع تولید»\n"
            f"📦 محصولاتت رو با «فروش کارخونه» بفروش!",
            reply_to_message_id=message_id
        )
        return True

    factory, result = _sync_and_get(user_data)
    db.set_key(sender_id, user_data)
    _send_status(user_data, factory, result, chat_id, message_id, bot)
    return True


def _send_status(user_data, factory, result, chat_id, message_id, bot):
    level = factory['level']
    capacity = warehouse_capacity(factory)
    stored = total_stored(factory)
    workers = factory.get('workers', 0)
    available_hire = available_workers_to_hire(user_data)
    cycle = cycle_seconds(factory)
    current_product = factory.get('current_product')

    message = f"🏭 کارخونه میویی شما\n\n"
    message += f"⭐️ سطح: {level} (تا سطح بعد: {factory['exp']:,}/{level_up_threshold(level):,} exp)\n"
    message += f"🐈 کارگران: {workers:,} (قابل استخدام: {available_hire:,})\n"
    message += f"⚙️ دستگاه: سطح {factory.get('machine_level',1)} (هر سیکل: {format_time(cycle)})\n"
    message += f"📦 انبار: {stored:,} / {capacity:,}\n"

    if current_product:
        pname = FACTORY_PRODUCTS[current_product]['name']
        message += f"🏗 در حال تولید: {pname}\n"
    else:
        message += f"🏗 در حال تولید: هیچی (بگو «شروع تولید»)\n"

    message += result and _production_notice(result) or ""

    if factory.get('stored_products'):
        message += "\n\n📦 موجودی انبار:\n"
        for pid, count in factory['stored_products'].items():
            if count > 0:
                price = get_product_price(pid)
                trend = get_price_trend_label(pid)
                message += f"┘─ {FACTORY_PRODUCTS[pid]['name']} × {count:,} — قیمت فعلی: {price:,} {trend}\n"

    message += "\nدستورات:\n"
    message += "┘─ «استخدام کارگر [عدد]» / «اخراج کارگر [عدد]»\n"
    message += "┘─ «شروع تولید»\n"
    message += "┘─ «ارتقا انبار» / «ارتقا دستگاه»\n"
    message += "┘─ «فروش کارخونه»\n"
    message += "┘─ «بازار کارخونه» (مشاهده قیمت‌ ها)"

    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)


# ============================================================
# استخدام / اخراج کارگر
# ============================================================

def handle_hire_worker(text, sender_id, message_id, chat_id, bot) -> bool:
    if not text.startswith(HIRE_PREFIX):
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    if not has_factory(user_data):
        bot.sendMessage(chat_id, "🏭 اول باید کارخونه بسازی! بگو «کارخونه میویی»", reply_to_message_id=message_id)
        return True

    raw = text[len(HIRE_PREFIX):].strip()
    if not raw.isdigit() or int(raw) <= 0:
        bot.sendMessage(chat_id, f"❌ فرمت درست: «{HIRE_PREFIX}[عدد]»", reply_to_message_id=message_id)
        return True

    requested = int(raw)
    available = available_workers_to_hire(user_data)

    if available <= 0:
        bot.sendMessage(
            chat_id,
            "❌ هیچ پیشی خیابونی آزادی برای استخدام نداری!\nبرو تو گروه‌ ها یه چندتا رو نجات بده 🐈",
            reply_to_message_id=message_id
        )
        return True

    hired = hire_workers(user_data, requested)
    db.set_key(sender_id, user_data)

    bot.sendMessage(
        chat_id,
        f"✅ {hired:,} کارگر جدید استخدام شد!\n"
        f"🐈 کل کارگران: {user_data['factory']['workers']:,}",
        reply_to_message_id=message_id
    )
    return True


def handle_fire_worker(text, sender_id, message_id, chat_id, bot) -> bool:
    if not text.startswith(FIRE_PREFIX):
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    if not has_factory(user_data):
        bot.sendMessage(chat_id, "🏭 اول باید کارخونه بسازی! بگو «کارخونه میویی»", reply_to_message_id=message_id)
        return True

    raw = text[len(FIRE_PREFIX):].strip()
    if not raw.isdigit() or int(raw) <= 0:
        bot.sendMessage(chat_id, f"❌ فرمت درست: «{FIRE_PREFIX}[عدد]»", reply_to_message_id=message_id)
        return True

    factory = user_data['factory']
    fired = fire_workers(factory, int(raw))
    db.set_key(sender_id, user_data)

    bot.sendMessage(
        chat_id,
        f"👋 {fired:,} کارگر اخراج شد.\n🐈 کارگران باقی‌مانده: {factory['workers']:,}",
        reply_to_message_id=message_id
    )
    return True


# ============================================================
# شروع تولید (کانورسیشن انتخاب محصول)
# ============================================================

def handle_start_production(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in START_PRODUCTION_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    if not has_factory(user_data):
        bot.sendMessage(chat_id, "🏭 اول باید کارخونه بسازی! بگو «کارخونه میویی»", reply_to_message_id=message_id)
        return True

    factory, result = _sync_and_get(user_data)
    db.set_key(sender_id, user_data)

    unlocked = get_unlocked_products(factory['level'])
    if not unlocked:
        bot.sendMessage(chat_id, "❌ هیچ محصولی هنوز باز نشده!", reply_to_message_id=message_id)
        return True

    message = "🏗 کدوم محصول رو تولید کنم؟\n\n"
    for idx, pid in enumerate(unlocked, 1):
        info = FACTORY_PRODUCTS[pid]
        price = get_product_price(pid)
        message += f"{idx}. {info['name']} — قیمت فعلی: {price:,} پوینت\n"
    message += "\n❌ برای انصراف بگو «لغو»"

    start_conversation(sender_id, CONV_PRODUCTION, step='select', data={'options': unlocked})
    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True


def _handle_production_conv(conv, text, sender_id, message_id, chat_id, bot) -> bool:
    options = conv.get('data', {}).get('options', [])
    choice = text.strip()

    if not choice.isdigit() or not (1 <= int(choice) <= len(options)):
        bot.sendMessage(chat_id, f"❌ یک عدد بین 1 تا {len(options)} بفرست یا بگو «لغو»", reply_to_message_id=message_id)
        return True

    product_id = options[int(choice) - 1]

    user_data = db.get_key(sender_id, {})
    if not has_factory(user_data):
        clear_conversation(sender_id)
        bot.sendMessage(chat_id, "❌ کارخونه‌ای پیدا نشد!", reply_to_message_id=message_id)
        return True

    factory = user_data['factory']
    factory['current_product'] = product_id
    factory['last_production_at'] = time.time()

    db.set_key(sender_id, user_data)
    clear_conversation(sender_id)

    bot.sendMessage(
        chat_id,
        f"✅ تولید {FACTORY_PRODUCTS[product_id]['name']} شروع شد!\n"
        f"⚙️ هر {format_time(cycle_seconds(factory))} به تعداد کارگرانت ({factory.get('workers',0):,}) محصول تولید میشه.\n"
        f"👉 برای دیدن پیشرفت بگو «کارخونه میویی»",
        reply_to_message_id=message_id
    )
    return True


# ============================================================
# ارتقا انبار / دستگاه
# ============================================================

def handle_upgrade_warehouse(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in UPGRADE_WAREHOUSE_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    if not has_factory(user_data):
        bot.sendMessage(chat_id, "🏭 اول باید کارخونه بسازی! بگو «کارخونه میویی»", reply_to_message_id=message_id)
        return True

    factory = user_data['factory']
    cost = warehouse_upgrade_cost(factory)

    if user_data.get('meow_points', 0) < cost:
        bot.sendMessage(chat_id, f"❌ پوینت کافی نداری!\n💰 هزینه: {cost:,} پوینت", reply_to_message_id=message_id)
        return True

    user_data['meow_points'] -= cost
    factory['warehouse_level'] += 1
    db.set_key(sender_id, user_data)

    bot.sendMessage(
        chat_id,
        f"🎉 انبار به سطح {factory['warehouse_level']} ارتقا یافت!\n"
        f"📦 ظرفیت جدید: {warehouse_capacity(factory):,}\n💰 هزینه: {cost:,} پوینت",
        reply_to_message_id=message_id
    )
    return True


def handle_upgrade_machine(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in UPGRADE_MACHINE_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    if not has_factory(user_data):
        bot.sendMessage(chat_id, "🏭 اول باید کارخونه بسازی! بگو «کارخونه میویی»", reply_to_message_id=message_id)
        return True

    factory = user_data['factory']
    cost = machine_upgrade_cost(factory)

    if user_data.get('meow_points', 0) < cost:
        bot.sendMessage(chat_id, f"❌ پوینت کافی نداری!\n💰 هزینه: {cost:,} پوینت", reply_to_message_id=message_id)
        return True

    if cycle_seconds(factory) <= 10:
        bot.sendMessage(chat_id, "🌟 دستگاهت همین الانم به سرعت نهایی رسیده!", reply_to_message_id=message_id)
        return True

    user_data['meow_points'] -= cost
    factory['machine_level'] += 1
    db.set_key(sender_id, user_data)

    bot.sendMessage(
        chat_id,
        f"🎉 دستگاه به سطح {factory['machine_level']} ارتقا یافت!\n"
        f"⚙️ زمان هر سیکل: {format_time(cycle_seconds(factory))}\n💰 هزینه: {cost:,} پوینت",
        reply_to_message_id=message_id
    )
    return True


# ============================================================
# فروش محصولات (کانورسیشن)
# ============================================================

def handle_sell_start(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in SELL_START_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    if not has_factory(user_data):
        bot.sendMessage(chat_id, "🏭 اول باید کارخونه بسازی! بگو «کارخونه میویی»", reply_to_message_id=message_id)
        return True

    factory, _ = _sync_and_get(user_data)
    db.set_key(sender_id, user_data)

    stored = {pid: c for pid, c in factory.get('stored_products', {}).items() if c > 0}
    if not stored:
        bot.sendMessage(chat_id, "❌ انبارت خالیه، چیزی برای فروش نداری!", reply_to_message_id=message_id)
        return True

    options = list(stored.keys())
    message = "💰 کدوم محصول رو بفروشم؟\n\n"
    for idx, pid in enumerate(options, 1):
        info = FACTORY_PRODUCTS[pid]
        price = get_product_price(pid)
        message += f"{idx}. {info['name']} — موجودی: {stored[pid]:,} — قیمت واحد: {price:,} پوینت\n"
    message += "\n❌ برای انصراف بگو «لغو»"

    start_conversation(sender_id, CONV_SELL, step='select', data={'options': options})
    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True


def _handle_sell_select_conv(conv, text, sender_id, message_id, chat_id, bot) -> bool:
    options = conv.get('data', {}).get('options', [])
    choice = text.strip()

    if not choice.isdigit() or not (1 <= int(choice) <= len(options)):
        bot.sendMessage(chat_id, f"❌ یک عدد بین 1 تا {len(options)} بفرست یا بگو «لغو»", reply_to_message_id=message_id)
        return True

    product_id = options[int(choice) - 1]

    user_data = db.get_key(sender_id, {})
    factory = user_data.get('factory', {})
    available = factory.get('stored_products', {}).get(product_id, 0)

    if available <= 0:
        clear_conversation(sender_id)
        bot.sendMessage(chat_id, "❌ این محصول دیگه توی انبارت نیست!", reply_to_message_id=message_id)
        return True

    update_conversation(sender_id, step='amount', data={'product_id': product_id})

    price = get_product_price(product_id)
    bot.sendMessage(
        chat_id,
        f"{FACTORY_PRODUCTS[product_id]['name']}\n"
        f"📦 موجودی: {available:,} | 💰 قیمت واحد فعلی: {price:,} پوینت\n\n"
        f"چند تا بفروشم؟ عدد بفرست یا بگو «همه»",
        reply_to_message_id=message_id
    )
    return True


def _handle_sell_amount_conv(conv, text, sender_id, message_id, chat_id, bot) -> bool:
    product_id = conv.get('data', {}).get('product_id')

    user_data = db.get_key(sender_id, {})
    factory = user_data.get('factory', {})
    available = factory.get('stored_products', {}).get(product_id, 0)

    if available <= 0:
        clear_conversation(sender_id)
        bot.sendMessage(chat_id, "❌ این محصول دیگه توی انبارت نیست!", reply_to_message_id=message_id)
        return True

    raw = text.strip()
    if raw in ("همه", "all", "همش"):
        amount = available
    elif raw.isdigit():
        amount = int(raw)
    else:
        bot.sendMessage(chat_id, "❌ یک عدد معتبر بفرست یا بگو «همه» یا «لغو»", reply_to_message_id=message_id)
        return True

    if amount <= 0 or amount > available:
        bot.sendMessage(chat_id, f"❌ مقدار باید بین 1 تا {available:,} باشه!", reply_to_message_id=message_id)
        return True

    unit_price = get_product_price(product_id)
    total_value = unit_price * amount

    factory['stored_products'][product_id] -= amount
    user_data['meow_points'] = user_data.get('meow_points', 0) + total_value

    db.set_key(sender_id, user_data)
    clear_conversation(sender_id)

    bot.sendMessage(
        chat_id,
        f"✅ فروش موفق!\n\n"
        f"{FACTORY_PRODUCTS[product_id]['name']} × {amount:,} عدد\n"
        f"💰 مبلغ دریافتی: {total_value:,} پوینت (واحد: {unit_price:,})\n"
        f"📊 موجودی جدید: {user_data['meow_points']:,} پوینت",
        reply_to_message_id=message_id
    )
    return True


def handle_factory_conversation(text, sender_id, message_id, chat_id, bot) -> bool:
    conv = get_conversation(sender_id)
    if not conv or conv.get('name') not in (CONV_PRODUCTION, CONV_SELL):
        return False

    if text.strip() in CANCEL_KEYWORDS:
        clear_conversation(sender_id)
        bot.sendMessage(chat_id, "❌ لغو شد.", reply_to_message_id=message_id)
        return True

    if conv['name'] == CONV_PRODUCTION:
        return _handle_production_conv(conv, text, sender_id, message_id, chat_id, bot)

    if conv['name'] == CONV_SELL:
        if conv.get('step') == 'select':
            return _handle_sell_select_conv(conv, text, sender_id, message_id, chat_id, bot)
        if conv.get('step') == 'amount':
            return _handle_sell_amount_conv(conv, text, sender_id, message_id, chat_id, bot)

    clear_conversation(sender_id)
    return False


# ============================================================
# مشاهده بازار
# ============================================================

def handle_market_view(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in MARKET_VIEW_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    prices = get_all_prices()

    message = "🛍 بازار کارخونه میویی\n\n"
    message += "💹 قیمت‌ ها هر ساعت بر اساس نوسان بازار و اقتصاد کل بازیکن‌ ها تغییر می‌کنن:\n\n"

    for pid, info in FACTORY_PRODUCTS.items():
        trend = get_price_trend_label(pid)
        message += f"{info['name']}\n┘─ قیمت فعلی: {prices[pid]:,} پوینت {trend} (پایه: {info['base_price']:,})\n\n"

    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True
