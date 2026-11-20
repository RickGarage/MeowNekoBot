# handlers/games/fishing.py
"""بازی ماهیگیری - صید، ذخیره ماهی در انبار و فروش به‌صورت کانورسیشن"""

import time
import random
from random import randint

from config import FISHING_MIN_USER_LEVEL

from core.db_instance import db
from core.helpers import check_user_registered, format_time, get_user_display_name
from core.conversations import (
    start_conversation,
    update_conversation,
    get_conversation,
    clear_conversation,
    is_in_conversation,
)
from core.roles import get_user_role,VALID_ROLES


STATS_KEYWORDS = ["fishing stats", "stats fishing", "آمار ماهیگیری", "ماهیگیری آمار"]
LEADERBOARD_KEYWORDS = ["fishing leaderboard", "fishing top", "لیدربرد ماهیگیری", "تاپ ماهیگیری"]
INVENTORY_KEYWORDS = ["انبار ماهی", "موجودی ماهی", "کوله ماهی", "fish inventory"]
SELL_START_KEYWORDS = ["فروش ماهی", "sell fish"]
CANCEL_KEYWORDS = ["لغو", "cancel", "انصراف"]

CONVERSATION_NAME = "fishing_sell"
MAX_INVENTORY_STACKS = 200

MEDALS = ["🥇", "🥈", "🥉", "🎖", "🏅"]
TITLES = ["پادشاه ماهیگیر", "ستاره دریا", "صیاد برتر", "ماهیگیر حرفه‌ای", "ماهیگیر مبتدی"]

FISHING_MESSAGES = [
    "🎣 قلاب رو انداختی تو آب...",
    "🌊 داره قلاب رو میکشه...",
    "🐟 یه ماهی گیر کردی!",
    "💪 چه صید خوبی!",
    "🌟 امروز روز خوبی برای ماهیگیریه!"
]


# ============================================================
# توابع کمکی انبار ماهی
# ============================================================

def _get_inventory(user_data):
    inventory = user_data.get('fish_inventory')
    if not isinstance(inventory, list):
        inventory = []
    return inventory


def _add_catch_to_inventory(user_data, name, unit_price, count, weight_each, is_rare):
    inventory = _get_inventory(user_data)

    # اگر آخرین دسته دقیقاً همین نوع و همین قیمت واحد را دارد، با آن ادغام کن
    if inventory and inventory[-1]['name'] == name and inventory[-1]['unit_price'] == unit_price:
        inventory[-1]['count'] += count
    else:
        inventory.append({
            'name': name,
            'unit_price': unit_price,
            'count': count,
            'weight_each': weight_each,
            'rare': is_rare,
        })

    # جلوگیری از رشد بی‌حد و حصر انبار
    if len(inventory) > MAX_INVENTORY_STACKS:
        inventory = inventory[-MAX_INVENTORY_STACKS:]

    user_data['fish_inventory'] = inventory
    return user_data


def _grouped_inventory(inventory):
    """گروه‌بندی موجودی بر اساس نام ماهی برای نمایش (تجمیع تعداد و ارزش)"""
    groups = {}
    order = []
    for stack in inventory:
        name = stack['name']
        if name not in groups:
            groups[name] = {'name': name, 'count': 0, 'total_value': 0, 'rare': stack.get('rare', False)}
            order.append(name)
        groups[name]['count'] += stack['count']
        groups[name]['total_value'] += stack['count'] * stack['unit_price']

    return [groups[name] for name in order]


def get_inventory_groups(user_data):
    """نسخه عمومی برای دسترسی سایر ماژول‌ها (مثل یخچال) به موجودی گروه‌بندی‌شده"""
    return _grouped_inventory(_get_inventory(user_data))


def _sell_from_inventory(inventory, name, amount):
    """
    فروش `amount` عدد از ماهی با نام `name` از داخل انبار (روش FIFO).
    Returns: (inventory_جدید, مبلغ_کل_فروش, تعداد_واقعی_فروخته_شده)
    """
    remaining_to_sell = amount
    total_value = 0
    new_inventory = []

    for stack in inventory:
        if remaining_to_sell <= 0 or stack['name'] != name:
            new_inventory.append(stack)
            continue

        sell_from_this = min(stack['count'], remaining_to_sell)
        total_value += sell_from_this * stack['unit_price']
        remaining_to_sell -= sell_from_this

        leftover = stack['count'] - sell_from_this
        if leftover > 0:
            new_stack = dict(stack)
            new_stack['count'] = leftover
            new_inventory.append(new_stack)

    sold_count = amount - remaining_to_sell
    return new_inventory, total_value, sold_count


def take_best_fish(user_data, name):
    """
    برداشتن یک واحد از باارزش‌ترین دسته موجود با نام مشخص (برای فریز کردن در یخچال).

    Returns:
        tuple(bool, Optional[float], Optional[float]): (موفقیت، unit_price، weight_each)
    """
    inventory = _get_inventory(user_data)
    matching_indices = [i for i, s in enumerate(inventory) if s['name'] == name and s['count'] > 0]
    if not matching_indices:
        return False, None, None

    best_idx = max(matching_indices, key=lambda i: inventory[i]['unit_price'])
    best_stack = inventory[best_idx]

    unit_price = best_stack['unit_price']
    weight_each = best_stack['weight_each']

    best_stack['count'] -= 1
    if best_stack['count'] <= 0:
        inventory.pop(best_idx)

    user_data['fish_inventory'] = inventory
    return True, unit_price, weight_each


def consume_fish_for_food(user_data, amount=1):
    """
    مصرف `amount` عدد ماهی (از هر نوع، قدیمی‌ترین دسته اول) برای تغذیه پیشی.

    Returns:
        tuple(bool, Optional[str]): (موفقیت، نام ماهی مصرف‌شده)
    """
    inventory = _get_inventory(user_data)
    if not inventory:
        return False, None

    remaining = amount
    consumed_name = None
    new_inventory = []

    for stack in inventory:
        if remaining <= 0:
            new_inventory.append(stack)
            continue

        take = min(stack['count'], remaining)
        if take > 0:
            consumed_name = stack['name']
            remaining -= take
            leftover = stack['count'] - take
            if leftover > 0:
                s = dict(stack)
                s['count'] = leftover
                new_inventory.append(s)
        else:
            new_inventory.append(stack)

    success = remaining < amount
    user_data['fish_inventory'] = new_inventory
    return success, consumed_name


def handle_fishing(text, sender_id, message_id, chat_id, bot) -> bool:
    if not (text.lower().startswith("fishing") or text.lower().startswith("ماهیگیری") or text.lower().startswith("ماهی")):
        return False

    # اگر کاربر وسط کانورسیشن فروشه، اجازه صید نده تا گیج نشه
    if is_in_conversation(sender_id, CONVERSATION_NAME):
        bot.sendMessage(
            chat_id,
            "🎣 اول فرآیند فروش ماهی رو تموم کن یا بگو «لغو»!",
            reply_to_message_id=message_id
        )
        return True

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    # دریافت اطلاعات کاربر
    user_data = db.get_key(sender_id, {})

    if not user_data:
            bot.sendMessage(
                chat_id,
                "❌ شما در دیتابیس ثبت نام نشده‌اید! لطفاً ربات را در پیوی استارت کنید.",
                reply_to_message_id=message_id
            )
            return True

    # کاربر پیشی نداره -> شروع فرآیند خرید
    user_level = user_data.get('meow_level', 1)

    if user_level < FISHING_MIN_USER_LEVEL:
        bot.sendMessage(
            chat_id,
            f"🔒 برای شرطبندی باید حداقل سطح {FISHING_MIN_USER_LEVEL} باشی!\n"
            f"⭐️ سطح فعلی تو : {user_level}",
            reply_to_message_id=message_id
        )
        return True

    # بررسی کول‌داون (6 دقیقه = 360 ثانیه)
    last_fishing = user_data.get('last_fishing', 0)
    current_time = time.time()
    user_role = get_user_role(sender_id)
    
    if user_role == VALID_ROLES[2]:
        cooldown_seconds = 30
    elif user_role == VALID_ROLES[3]:
        cooldown_seconds = 0
    else:
        cooldown_seconds = 360

    if current_time - last_fishing < cooldown_seconds:
        remaining = int(cooldown_seconds - (current_time - last_fishing))
        formatted_time = format_time(remaining)
        bot.sendMessage(
            chat_id,
            f"🎣 هنوز زمان ماهیگیری تموم نشده!\n"
            f"⏳ باید {formatted_time} صبر کنی تا دوباره بتونی ماهیگیری کنی.",
            reply_to_message_id=message_id
        )
        return True

    # دریافت سطح کاربر برای ضریب
    user_level = user_data.get('meow_level', 1)

    # تعداد ماهی صید شده (بین 5 تا 15)
    fish_count = randint(5, 15)

    # شانس صید ماهی نادر (10% شانس)
    is_rare_fish = random.random() < 0.1

    # تعیین ضریب قیمت (بین 1 تا 5 بر اساس سطح کاربر)
    max_multiplier = min(user_level, 5)
    min_multiplier = 1

    if random.random() < 0.3:
        multiplier = round(random.uniform(min_multiplier, 2), 1)
    elif random.random() < 0.6:
        multiplier = round(random.uniform(2, 3.5), 1)
    else:
        multiplier = round(random.uniform(3.5, max_multiplier), 1)

    multiplier = min(multiplier, max_multiplier)

    # قیمت پایه هر ماهی (بین 100 تا 250)
    base_price = randint(100, 250)

    if is_rare_fish:
        base_price = base_price * 3
        fish_name = "🐟 ماهی طلایی نادر"
        weight_each = round(random.uniform(1.5, 5.0), 2)
    else:
        fish_name = "🐠 ماهی معمولی"
        weight_each = round(random.uniform(0.05, 1.5), 2)

    unit_price = int(base_price * multiplier)
    potential_value = unit_price * fish_count

    # اضافه شدن به انبار (ذخیره خودکار - دیگه فورا فروخته نمیشه)
    user_data = _add_catch_to_inventory(user_data, fish_name, unit_price, fish_count, weight_each, is_rare_fish)

    user_data['last_fishing'] = current_time
    user_data['fishing_total'] = user_data.get('fishing_total', 0) + 1
    user_data['fishing_total_fish'] = user_data.get('fishing_total_fish', 0) + fish_count

    if is_rare_fish:
        user_data['fishing_rare_fish'] = user_data.get('fishing_rare_fish', 0) + 1

    db.set_key(sender_id, user_data)

    result_message = f"🎣 ماهیگیری!\n\n"
    result_message += f"{random.choice(FISHING_MESSAGES)}\n"
    result_message += f"🐟 تعداد ماهی: {fish_count} عدد\n"
    result_message += f"🎣 نوع ماهی: {fish_name}\n"
    result_message += f"⚖️ وزن هر ماهی: {weight_each} کیلوگرم\n"
    result_message += f"💰 قیمت هر ماهی: {unit_price:,} پوینت\n"
    result_message += f"🎯 ضریب: {multiplier}x\n"
    result_message += f"📦 ارزش این صید: {potential_value:,} پوینت (توی انبارت ذخیره شد)\n\n"

    inventory_count = sum(s['count'] for s in _get_inventory(user_data))
    result_message += f"🧳 کل ماهی‌های انبارت: {inventory_count} عدد\n"
    result_message += f"👉 برای فروش بگو «فروش ماهی»"

    bot.sendMessage(chat_id, result_message, reply_to_message_id=message_id)

    fishing_history = db.get_key("fishing_history", [])
    fishing_history.append({
        'user_id': sender_id,
        'fish_count': fish_count,
        'unit_price': unit_price,
        'multiplier': multiplier,
        'potential_value': potential_value,
        'is_rare': is_rare_fish,
        'time': current_time
    })
    if len(fishing_history) > 200:
        fishing_history = fishing_history[-200:]
    db.set_key("fishing_history", fishing_history)

    return True


# ============================================================
# نمایش انبار ماهی
# ============================================================

def handle_fish_inventory(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.lower() not in INVENTORY_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    inventory = _get_inventory(user_data)
    groups = _grouped_inventory(inventory)

    if not groups:
        bot.sendMessage(
            chat_id,
            "🧳 انبار ماهیت خالیه! برو یه دستی ماهیگیری کن 🎣\nبگو «ماهیگیری»",
            reply_to_message_id=message_id
        )
        return True

    message = "🧳 انبار ماهی تو 🐟\n\n"
    total_value = 0
    for idx, g in enumerate(groups, 1):
        message += f"{idx}. {g['name']}\n"
        message += f"┘─ تعداد: {g['count']:,} عدد | ارزش تقریبی: {g['total_value']:,} پوینت\n\n"
        total_value += g['total_value']

    message += f"💰 ارزش کل انبار: {total_value:,} پوینت\n"
    message += f"👉 برای فروش بگو «فروش ماهی»"

    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True


# ============================================================
# کانورسیشن فروش ماهی
# ============================================================

def handle_sell_fish_start(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.lower() not in SELL_START_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    inventory = _get_inventory(user_data)
    groups = _grouped_inventory(inventory)

    if not groups:
        bot.sendMessage(
            chat_id,
            "🧳 انبار ماهیت خالیه! چیزی برای فروش نداری.\nبرو یه دستی ماهیگیری کن 🎣",
            reply_to_message_id=message_id
        )
        return True

    message = "🛒 فروش ماهی 🐟\n\nکدوم ماهی رو میخوای بفروشی؟ عدد مربوطه رو بفرست:\n\n"
    for idx, g in enumerate(groups, 1):
        message += f"{idx}. {g['name']} — موجودی: {g['count']:,} | ارزش کل: {g['total_value']:,} پوینت\n"
    message += "\n❌ برای انصراف بگو «لغو»"

    start_conversation(
        sender_id,
        CONVERSATION_NAME,
        step='select_fish',
        data={'options': [g['name'] for g in groups]}
    )

    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True


def handle_fishing_conversation(text, sender_id, message_id, chat_id, bot) -> bool:
    """پردازش مراحل بعدی کانورسیشن فروش ماهی (باید قبل از سایر هندلرها فراخوانی شود)"""
    conv = get_conversation(sender_id)
    if not conv or conv.get('name') != CONVERSATION_NAME:
        return False

    if text.lower() in CANCEL_KEYWORDS:
        clear_conversation(sender_id)
        bot.sendMessage(chat_id, "❌ فرآیند فروش ماهی لغو شد.", reply_to_message_id=message_id)
        return True

    step = conv.get('step')
    data = conv.get('data', {})

    if step == 'select_fish':
        options = data.get('options', [])
        choice = text.strip()

        if not choice.isdigit() or not (1 <= int(choice) <= len(options)):
            bot.sendMessage(
                chat_id,
                f"❌ لطفاً یک عدد بین 1 تا {len(options)} بفرست، یا بگو «لغو»",
                reply_to_message_id=message_id
            )
            return True

        selected_name = options[int(choice) - 1]

        user_data = db.get_key(sender_id, {})
        groups = _grouped_inventory(_get_inventory(user_data))
        selected_group = next((g for g in groups if g['name'] == selected_name), None)

        if not selected_group or selected_group['count'] <= 0:
            clear_conversation(sender_id)
            bot.sendMessage(chat_id, "❌ این ماهی دیگه توی انبارت نیست!", reply_to_message_id=message_id)
            return True

        update_conversation(sender_id, step='select_amount', data={'selected_name': selected_name})

        bot.sendMessage(
            chat_id,
            f"🐟 {selected_name}\n"
            f"📦 موجودی: {selected_group['count']:,} عدد\n\n"
            f"چند تا میخوای بفروشی؟ عدد بفرست یا بگو «همه»",
            reply_to_message_id=message_id
        )
        return True

    if step == 'select_amount':
        selected_name = data.get('selected_name')

        user_data = db.get_key(sender_id, {})
        inventory = _get_inventory(user_data)
        groups = _grouped_inventory(inventory)
        selected_group = next((g for g in groups if g['name'] == selected_name), None)

        if not selected_group or selected_group['count'] <= 0:
            clear_conversation(sender_id)
            bot.sendMessage(chat_id, "❌ این ماهی دیگه توی انبارت نیست!", reply_to_message_id=message_id)
            return True

        available = selected_group['count']
        raw = text.strip()

        if raw in ("همه", "all", "همش"):
            amount = available
        elif raw.isdigit():
            amount = int(raw)
        else:
            bot.sendMessage(
                chat_id,
                "❌ لطفاً یک عدد معتبر بفرست یا بگو «همه» یا «لغو»",
                reply_to_message_id=message_id
            )
            return True

        if amount <= 0 or amount > available:
            bot.sendMessage(
                chat_id,
                f"❌ مقدار باید بین 1 تا {available:,} باشه!",
                reply_to_message_id=message_id
            )
            return True

        new_inventory, total_value, sold_count = _sell_from_inventory(inventory, selected_name, amount)

        user_data['fish_inventory'] = new_inventory
        user_data['meow_points'] = user_data.get('meow_points', 0) + total_value
        user_data['fishing_total_earn'] = user_data.get('fishing_total_earn', 0) + total_value

        db.set_key(sender_id, user_data)
        clear_conversation(sender_id)

        bot.sendMessage(
            chat_id,
            f"✅ فروش موفق!\n\n"
            f"🐟 {selected_name} × {sold_count:,} عدد فروخته شد\n"
            f"💰 مبلغ دریافتی: {total_value:,} پوینت\n"
            f"📊 موجودی جدید: {user_data['meow_points']:,} پوینت",
            reply_to_message_id=message_id
        )
        return True

    # حالت نامعتبر/ناشناخته - برای احتیاط کانورسیشن را پاک کن
    clear_conversation(sender_id)
    return False


# ============================================================
# آمار و لیدربرد ماهیگیری
# ============================================================

def handle_fishing_stats(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.lower() not in STATS_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    if not user_data:
        bot.sendMessage(
            chat_id,
            "❌ شما در دیتابیس ثبت نام نشده‌اید!",
            reply_to_message_id=message_id
        )
        return True

    total_fishing = user_data.get('fishing_total', 0)
    total_fish = user_data.get('fishing_total_fish', 0)
    total_earn = user_data.get('fishing_total_earn', 0)
    rare_fish = user_data.get('fishing_rare_fish', 0)
    inventory_value = sum(g['total_value'] for g in _grouped_inventory(_get_inventory(user_data)))

    avg_fish = (total_fish / total_fishing) if total_fishing > 0 else 0
    avg_earn = (total_earn / total_fishing) if total_fishing > 0 else 0

    bot.sendMessage(
        chat_id,
        f"🎣 آمار ماهیگیری شما:\n\n"
        f"📊 تعداد صیدها: {total_fishing}\n"
        f"🐟 کل ماهی‌ها: {total_fish}\n"
        f"📈 میانگین ماهی در هر صید: {avg_fish:.1f}\n"
        f"💰 کل سود از فروش: {total_earn:,} پوینت\n"
        f"📈 میانگین سود در هر صید: {avg_earn:,.0f} پوینت\n"
        f"🧳 ارزش انبار فعلی: {inventory_value:,} پوینت\n"
        f"🌟 ماهی طلایی: {rare_fish}",
        reply_to_message_id=message_id
    )
    return True


def handle_fishing_leaderboard(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.lower() not in LEADERBOARD_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    all_users = db.get_all_keys()
    fishing_stats = []

    for uid in all_users:
        if not uid:
            continue
        if uid.startswith('u') or uid.startswith('b'):
            data = db.get_key(uid, {})
            if isinstance(data, dict) and data:
                total_fish = data.get('fishing_total_fish', 0)
                total_earn = data.get('fishing_total_earn', 0)
                if total_fish > 0 or total_earn > 0:
                    fishing_stats.append((uid, total_fish, total_earn, data))

    fishing_stats.sort(key=lambda x: x[2], reverse=True)
    top_users = fishing_stats[:5]

    if not top_users:
        bot.sendMessage(
            chat_id,
            "🎣 هنوز کسی ماهیگیری نکرده! اولین نفر باش!",
            reply_to_message_id=message_id
        )
        return True

    message = "🎣 لیدربرد ماهیگیری 🏆\n\n"
    message += "💰 بر اساس کل سود فروش\n\n"

    for idx, (uid, total_fish, total_earn, data) in enumerate(top_users):
        medal = MEDALS[idx] if idx < len(MEDALS) else f"#{idx+1}"
        title = TITLES[idx] if idx < len(TITLES) else "ماهیگیر"

        display_name = get_user_display_name(bot, uid)
        total_fishing = data.get('fishing_total', 0)
        rare_fish = data.get('fishing_rare_fish', 0)

        message += f"{medal} {title} : {display_name}\n"
        message += f"┘─ 💰 کل سود: {total_earn:,} پوینت\n"
        message += f"┘─ 🐟 کل ماهی‌ها: {total_fish}\n"
        message += f"┘─ 🎣 تعداد صیدها: {total_fishing}\n"
        if rare_fish > 0:
            message += f"┘─ 🌟 ماهی طلایی: {rare_fish}\n"
        message += "\n"

    user_rank = 0
    for idx, (uid, _, _, _) in enumerate(fishing_stats, 1):
        if uid == sender_id:
            user_rank = idx
            break

    if user_rank > 0:
        message += f"🎖️ رتبه شما: #{user_rank:,}\n"
        user_data = db.get_key(sender_id, {})
        message += f"💰 کل سود شما: {user_data.get('fishing_total_earn', 0):,} پوینت"

    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True
