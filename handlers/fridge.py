# handlers/fridge.py
"""هندلر یخچال میویی - ذخیره یک واحد از هر نوع ماهی، پخت‌وپز و استفاده از ماهی‌های ذخیره‌شده"""

import time

from core.db_instance import db
from core.helpers import check_user_registered, format_time
from core.conversations import start_conversation, get_conversation, clear_conversation
from core.fridge import (
    FRIDGE_UNLOCK_LEVEL,
    has_fridge_access,
    get_fridge,
    get_fridge_capacity,
    fridge_upgrade_cost,
    find_slot_index,
    cook_time_seconds,
    sync_cooking,
    sync_all_fridge,
    effective_sell_price,
    effective_feed_multiplier,
    create_fridge_entry,
)
from core.pet_engine import has_pet, update_pet_production, get_max_banked_energy
from config import PET_FEED_ENERGY_SECONDS
from handlers.games.fishing import get_inventory_groups, take_best_fish

VIEW_KEYWORDS = ["یخچال", "یخچال من", "fridge"]
STORE_START_KEYWORDS = ["ذخیره یخچال", "فریز ماهی"]
COOK_START_KEYWORDS = ["پخت ماهی", "پخت یخچال"]
SELL_START_KEYWORDS = ["فروش یخچال"]
FEED_START_KEYWORDS = ["تغذیه یخچال", "غذا یخچال"]
UPGRADE_KEYWORDS = ["ارتقا یخچال"]
CANCEL_KEYWORDS = ["لغو", "cancel", "انصراف"]

CONV_STORE = "fridge_store"
CONV_COOK = "fridge_cook"
CONV_SELL = "fridge_sell"
CONV_FEED = "fridge_feed"


def _locked_message():
    return f"❄️ یخچال میویی از سطح {FRIDGE_UNLOCK_LEVEL} فعال میشه!\nبیشتر میو کن تا سطحت بالا بره 🐾"


def _slot_status_line(idx, entry):
    name = entry['name']
    if entry.get('cooked'):
        return f"{idx}. {name} 🍳 (پخته‌شده - آماده فروش/تغذیه با ارزش بالا)"
    if entry.get('cooking'):
        remaining = max(0, int(entry.get('cook_ready_at', 0) - time.time()))
        return f"{idx}. {name} 🔥 (در حال پخت - {format_time(remaining)} مونده)"
    return f"{idx}. {name} ❄️ (خام - قیمت پایه: {entry['unit_price']:,} پوینت)"


# ============================================================
# نمایش یخچال
# ============================================================

def handle_fridge_view(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in VIEW_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})

    if not has_fridge_access(user_data):
        bot.sendMessage(chat_id, _locked_message(), reply_to_message_id=message_id)
        return True

    fridge = get_fridge(user_data)
    sync_all_fridge(fridge)
    db.set_key(sender_id, user_data)

    capacity = get_fridge_capacity(user_data)

    if not fridge:
        message = (
            f"❄️ یخچال میویی 🧊\n\n"
            f"📦 ظرفیت: 0 / {capacity}\n\n"
            f"هنوز چیزی ذخیره نکردی! برای فریز کردن یه ماهی بگو «ذخیره یخچال»"
        )
        bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
        return True

    message = f"❄️ یخچال میویی 🧊\n\n📦 ظرفیت: {len(fridge)} / {capacity}\n\n"
    for idx, entry in enumerate(fridge, 1):
        message += _slot_status_line(idx, entry) + "\n"

    message += "\nدستورات:\n"
    message += "┘─ «ذخیره یخچال» ❄️ (اگه جا داری)\n"
    message += "┘─ «پخت ماهی» 🔥\n"
    message += "┘─ «فروش یخچال» 💰\n"
    message += "┘─ «تغذیه یخچال» 🍖\n"
    message += "┘─ «ارتقا یخچال» 📈"

    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True


# ============================================================
# ذخیره (فریز کردن)
# ============================================================

def handle_fridge_store_start(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in STORE_START_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    if not has_fridge_access(user_data):
        bot.sendMessage(chat_id, _locked_message(), reply_to_message_id=message_id)
        return True

    fridge = get_fridge(user_data)
    capacity = get_fridge_capacity(user_data)

    if len(fridge) >= capacity:
        bot.sendMessage(
            chat_id,
            f"❌ یخچالت پره! ({len(fridge)}/{capacity})\nبرای جا باز کردن بگو «فروش یخچال» یا «ارتقا یخچال»",
            reply_to_message_id=message_id
        )
        return True

    frozen_names = {e['name'] for e in fridge}
    groups = [g for g in get_inventory_groups(user_data) if g['name'] not in frozen_names]

    if not groups:
        bot.sendMessage(
            chat_id,
            "❌ ماهی جدیدی برای ذخیره نداری (یا از هر نوعی که داری، یکیش قبلاً توی یخچاله)!",
            reply_to_message_id=message_id
        )
        return True

    message = "❄️ کدوم ماهی رو فریز کنم؟ (باارزش‌ترین واحدش انتخاب میشه)\n\n"
    for idx, g in enumerate(groups, 1):
        message += f"{idx}. {g['name']} — موجودی: {g['count']:,}\n"
    message += "\n❌ برای انصراف بگو «لغو»"

    start_conversation(sender_id, CONV_STORE, step='select', data={'options': [g['name'] for g in groups]})
    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True


def _handle_fridge_store_conv(conv, text, sender_id, message_id, chat_id, bot) -> bool:
    options = conv.get('data', {}).get('options', [])
    choice = text.strip()

    if not choice.isdigit() or not (1 <= int(choice) <= len(options)):
        bot.sendMessage(chat_id, f"❌ یک عدد بین 1 تا {len(options)} بفرست یا بگو «لغو»", reply_to_message_id=message_id)
        return True

    name = options[int(choice) - 1]
    user_data = db.get_key(sender_id, {})

    fridge = get_fridge(user_data)
    capacity = get_fridge_capacity(user_data)
    if len(fridge) >= capacity or find_slot_index(fridge, name) is not None:
        clear_conversation(sender_id)
        bot.sendMessage(chat_id, "❌ دیگه امکان ذخیره این ماهی نیست!", reply_to_message_id=message_id)
        return True

    success, unit_price, weight = take_best_fish(user_data, name)
    if not success:
        clear_conversation(sender_id)
        db.set_key(sender_id, user_data)
        bot.sendMessage(chat_id, "❌ این ماهی دیگه توی انبارت نیست!", reply_to_message_id=message_id)
        return True

    fridge.append(create_fridge_entry(name, unit_price, weight))
    user_data['fridge'] = fridge
    db.set_key(sender_id, user_data)
    clear_conversation(sender_id)

    bot.sendMessage(
        chat_id,
        f"❄️ {name} با موفقیت فریز شد!\n"
        f"💰 قیمت پایه: {unit_price:,} پوینت | ⚖️ وزن: {weight} کیلوگرم\n"
        f"👉 برای افزایش ۱۰ برابری قیمت، بگو «پخت ماهی»",
        reply_to_message_id=message_id
    )
    return True


# ============================================================
# پخت‌وپز
# ============================================================

def handle_fridge_cook_start(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in COOK_START_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    if not has_fridge_access(user_data):
        bot.sendMessage(chat_id, _locked_message(), reply_to_message_id=message_id)
        return True

    fridge = get_fridge(user_data)
    sync_all_fridge(fridge)
    db.set_key(sender_id, user_data)

    eligible = [(i, e) for i, e in enumerate(fridge) if not e.get('cooking') and not e.get('cooked')]
    if not eligible:
        bot.sendMessage(chat_id, "❌ ماهی خامی توی یخچالت نیست که بشه پخت!", reply_to_message_id=message_id)
        return True

    message = "🔥 کدوم ماهی رو بپزم؟\n\n"
    for idx, (fi, e) in enumerate(eligible, 1):
        t = cook_time_seconds(e['weight'])
        message += f"{idx}. {e['name']} — زمان پخت: {format_time(t)}\n"
    message += "\n❌ برای انصراف بگو «لغو»"

    start_conversation(sender_id, CONV_COOK, step='select', data={'fridge_indices': [fi for fi, _ in eligible]})
    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True


def _handle_fridge_cook_conv(conv, text, sender_id, message_id, chat_id, bot) -> bool:
    fridge_indices = conv.get('data', {}).get('fridge_indices', [])
    choice = text.strip()

    if not choice.isdigit() or not (1 <= int(choice) <= len(fridge_indices)):
        bot.sendMessage(chat_id, f"❌ یک عدد بین 1 تا {len(fridge_indices)} بفرست یا بگو «لغو»", reply_to_message_id=message_id)
        return True

    target_idx = fridge_indices[int(choice) - 1]

    user_data = db.get_key(sender_id, {})
    fridge = get_fridge(user_data)

    if target_idx >= len(fridge) or fridge[target_idx].get('cooking') or fridge[target_idx].get('cooked'):
        clear_conversation(sender_id)
        db.set_key(sender_id, user_data)
        bot.sendMessage(chat_id, "❌ این ماهی دیگه قابل پخت نیست!", reply_to_message_id=message_id)
        return True

    entry = fridge[target_idx]
    t = cook_time_seconds(entry['weight'])
    entry['cooking'] = True
    entry['cook_ready_at'] = time.time() + t

    db.set_key(sender_id, user_data)
    clear_conversation(sender_id)

    bot.sendMessage(
        chat_id,
        f"🔥 پخت {entry['name']} شروع شد!\n"
        f"⌛️ آماده میشه تا: {format_time(t)}\n"
        f"وقتی آماده شد، قیمت فروشش 10 برابر و قدرت سیرکنندگیش 2 برابر میشه! 🍳",
        reply_to_message_id=message_id
    )
    return True


# ============================================================
# فروش از یخچال
# ============================================================

def handle_fridge_sell_start(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in SELL_START_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    if not has_fridge_access(user_data):
        bot.sendMessage(chat_id, _locked_message(), reply_to_message_id=message_id)
        return True

    fridge = get_fridge(user_data)
    sync_all_fridge(fridge)
    db.set_key(sender_id, user_data)

    if not fridge:
        bot.sendMessage(chat_id, "❌ یخچالت خالیه!", reply_to_message_id=message_id)
        return True

    message = "💰 کدوم ماهی رو بفروشم؟\n\n"
    for idx, e in enumerate(fridge, 1):
        price = effective_sell_price(e)
        tag = " 🍳 پخته" if e.get('cooked') else ""
        message += f"{idx}. {e['name']}{tag} — قیمت: {price:,} پوینت\n"
    message += "\n❌ برای انصراف بگو «لغو»"

    start_conversation(sender_id, CONV_SELL, step='select')
    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True


def _handle_fridge_sell_conv(conv, text, sender_id, message_id, chat_id, bot) -> bool:
    user_data = db.get_key(sender_id, {})
    fridge = get_fridge(user_data)
    choice = text.strip()

    if not choice.isdigit() or not (1 <= int(choice) <= len(fridge)):
        bot.sendMessage(chat_id, f"❌ یک عدد بین 1 تا {len(fridge)} بفرست یا بگو «لغو»", reply_to_message_id=message_id)
        return True

    idx = int(choice) - 1
    entry = fridge.pop(idx)
    price = effective_sell_price(entry)

    user_data['fridge'] = fridge
    user_data['meow_points'] = user_data.get('meow_points', 0) + price
    user_data['fishing_total_earn'] = user_data.get('fishing_total_earn', 0) + price

    db.set_key(sender_id, user_data)
    clear_conversation(sender_id)

    tag = " پخته‌شده 🍳" if entry.get('cooked') else ""
    bot.sendMessage(
        chat_id,
        f"✅ {entry['name']}{tag} فروخته شد!\n"
        f"💰 مبلغ دریافتی: {price:,} پوینت\n"
        f"📊 موجودی جدید: {user_data['meow_points']:,} پوینت",
        reply_to_message_id=message_id
    )
    return True


# ============================================================
# تغذیه پیشی با ماهی یخچال
# ============================================================

def handle_fridge_feed_start(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in FEED_START_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    if not has_fridge_access(user_data):
        bot.sendMessage(chat_id, _locked_message(), reply_to_message_id=message_id)
        return True

    if not has_pet(user_data):
        bot.sendMessage(chat_id, "🐈 هنوز پیشی نداری! بگو «پیشی» تا یکی بخری.", reply_to_message_id=message_id)
        return True

    fridge = get_fridge(user_data)
    sync_all_fridge(fridge)
    db.set_key(sender_id, user_data)

    if not fridge:
        bot.sendMessage(chat_id, "❌ یخچالت خالیه!", reply_to_message_id=message_id)
        return True

    message = "🍖 با کدوم ماهی پیشی رو تغذیه کنم؟\n\n"
    for idx, e in enumerate(fridge, 1):
        tag = " 🍳 (انرژی دوبرابر!)" if e.get('cooked') else ""
        message += f"{idx}. {e['name']}{tag}\n"
    message += "\n❌ برای انصراف بگو «لغو»"

    start_conversation(sender_id, CONV_FEED, step='select')
    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True


def _handle_fridge_feed_conv(conv, text, sender_id, message_id, chat_id, bot) -> bool:
    user_data = db.get_key(sender_id, {})
    fridge = get_fridge(user_data)
    choice = text.strip()

    if not choice.isdigit() or not (1 <= int(choice) <= len(fridge)):
        bot.sendMessage(chat_id, f"❌ یک عدد بین 1 تا {len(fridge)} بفرست یا بگو «لغو»", reply_to_message_id=message_id)
        return True

    idx = int(choice) - 1
    entry = fridge.pop(idx)

    pet = user_data.get('pet')
    if not pet:
        clear_conversation(sender_id)
        db.set_key(sender_id, user_data)
        bot.sendMessage(chat_id, "❌ پیشی‌ای پیدا نشد!", reply_to_message_id=message_id)
        return True

    pet = update_pet_production(pet)

    multiplier = effective_feed_multiplier(entry)
    energy_seconds = PET_FEED_ENERGY_SECONDS * multiplier
    now = time.time()
    max_energy = get_max_banked_energy(pet)
    base_point = now if pet.get('energy_until', 0) < now else pet.get('energy_until', 0)
    pet['energy_until'] = min(base_point + energy_seconds, now + max_energy)

    user_data['pet'] = pet
    user_data['fridge'] = fridge
    db.set_key(sender_id, user_data)
    clear_conversation(sender_id)

    tag = " پخته‌شده 🍳" if entry.get('cooked') else ""
    bot.sendMessage(
        chat_id,
        f"😻 پیشیت با اشتها {entry['name']}{tag} رو خورد!\n"
        f"⚡️ {energy_seconds // 3600} ساعت بهش انرژی اضافه شد.",
        reply_to_message_id=message_id
    )
    return True


# ============================================================
# دیسپچر کانورسیشن‌های یخچال
# ============================================================

def handle_fridge_conversation(text, sender_id, message_id, chat_id, bot) -> bool:
    conv = get_conversation(sender_id)
    if not conv:
        return False

    name = conv.get('name')
    if name not in (CONV_STORE, CONV_COOK, CONV_SELL, CONV_FEED):
        return False

    if text.strip() in CANCEL_KEYWORDS:
        clear_conversation(sender_id)
        bot.sendMessage(chat_id, "❌ لغو شد.", reply_to_message_id=message_id)
        return True

    if name == CONV_STORE:
        return _handle_fridge_store_conv(conv, text, sender_id, message_id, chat_id, bot)
    if name == CONV_COOK:
        return _handle_fridge_cook_conv(conv, text, sender_id, message_id, chat_id, bot)
    if name == CONV_SELL:
        return _handle_fridge_sell_conv(conv, text, sender_id, message_id, chat_id, bot)
    if name == CONV_FEED:
        return _handle_fridge_feed_conv(conv, text, sender_id, message_id, chat_id, bot)

    clear_conversation(sender_id)
    return False


# ============================================================
# ارتقای ظرفیت یخچال
# ============================================================

def handle_fridge_upgrade(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in UPGRADE_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    if not has_fridge_access(user_data):
        bot.sendMessage(chat_id, _locked_message(), reply_to_message_id=message_id)
        return True

    capacity = get_fridge_capacity(user_data)
    cost = fridge_upgrade_cost(capacity)
    user_points = user_data.get('meow_points', 0)

    if user_points < cost:
        bot.sendMessage(
            chat_id,
            f"❌ پوینت کافی نداری!\n💰 هزینه ارتقا: {cost:,} پوینت\n📊 موجودی: {user_points:,} پوینت",
            reply_to_message_id=message_id
        )
        return True

    user_data['meow_points'] = user_points - cost
    user_data['fridge_capacity'] = capacity + 1
    db.set_key(sender_id, user_data)

    bot.sendMessage(
        chat_id,
        f"🎉 ظرفیت یخچال به {capacity + 1} رسید!\n💰 هزینه پرداختی: {cost:,} پوینت",
        reply_to_message_id=message_id
    )
    return True
