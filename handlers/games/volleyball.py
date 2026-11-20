# handlers/games/volleyball.py
"""بازی شرط‌بندی والیبال"""

import time
import random
from random import randint

from config import GAMELS_MIN_USER_LEVEL

from core.db_instance import db
from core.helpers import check_user_registered, format_time
from core.roles import get_user_role,VALID_ROLES

WIN_MESSAGES = [
    "🏐 اسپک! برد!",
    "🌟 ست رو بردی!",
    "🔥 دفاع عالی! برد!",
    "💪 تیمت برنده شد!",
    "🎯 سرویس طلایی!"
]

LOSS_MESSAGES = [
    "😢 توپ به تور خورد! باختی!",
    "💔 حریف بهتر بود!",
    "😅 ست رو باختی!",
    "🤷‍♂️ روزت نبود!",
    "🏐 نزدیک بود! بازم تلاش کن!"
]


def handle_volleyball(text, sender_id, message_id, chat_id, bot) -> bool:
    if not (text.lower().startswith("volleyball") or text.lower().startswith("والیبال")):
        return False

    # بررسی ثبت نام کاربر
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

    if user_level < GAMELS_MIN_USER_LEVEL:
        bot.sendMessage(
            chat_id,
            f"🔒 برای شرطبندی باید حداقل سطح {GAMELS_MIN_USER_LEVEL} باشی!\n"
            f"⭐️ سطح فعلی تو : {user_level}",
            reply_to_message_id=message_id
        )
        return True

    # بررسی کول‌داون (1.5 دقیقه = 90 ثانیه)
    last_volleyball = user_data.get('last_volleyball', 0)
    current_time = time.time()
    user_role = get_user_role(sender_id)
    
    if user_role == VALID_ROLES[2]:
        cooldown_seconds = 30
    elif user_role == VALID_ROLES[3]:
        cooldown_seconds = 0
    else:
        cooldown_seconds = 90

    if current_time - last_volleyball < cooldown_seconds:
        remaining = int(cooldown_seconds - (current_time - last_volleyball))
        formatted_time = format_time(remaining)
        bot.sendMessage(
            chat_id,
            f"🏐 هنوز زمان والیبال تموم نشده!\n"
            f"⏳ باید {formatted_time} صبر کنی تا دوباره بتونی بازی کنی.",
            reply_to_message_id=message_id
        )
        return True

    # استخراج مقدار شرط
    text_parts = text.split()
    if len(text_parts) < 2:
        bot.sendMessage(
            chat_id,
            "🏐 برای بازی والیبال باید مقدار پوینت رو وارد کنی!\n"
            "مثال: volleyball 50\n"
            "محدوده: 10 تا 50000 پوینت",
            reply_to_message_id=message_id
        )
        return True

    try:
        bet_amount = int(text_parts[1])
    except ValueError:
        bot.sendMessage(
            chat_id,
            "❌ مقدار وارد شده معتبر نیست! لطفاً یک عدد وارد کن.",
            reply_to_message_id=message_id
        )
        return True

    # بررسی محدوده شرط
    if bet_amount < 10 or bet_amount > 50000:
        bot.sendMessage(
            chat_id,
            "❌ مقدار شرط باید بین 10 تا 50000 باشد!",
            reply_to_message_id=message_id
        )
        return True

    user_points = user_data.get('meow_points', 0)

    # بررسی موجودی کاربر
    if bet_amount > user_points:
        bot.sendMessage(
            chat_id,
            f"❌ پوینت کافی نداری!\n"
            f"💰 پوینت شما: {user_points:,}\n"
            f"📤 پوینت مورد نیاز: {bet_amount:,}",
            reply_to_message_id=message_id
        )
        return True

    # دریافت سطح کاربر برای ضریب
    user_level = user_data.get('meow_level', 1)

    # محاسبه ضریب والیبال (1.2 تا سطح کاربر * 0.7)
    max_multiplier = min(user_level * 0.7, 7)  # حداکثر 7
    min_multiplier = 1.2

    # شانس ضریب‌ها
    if random.random() < 0.35:  # 35% شانس ضریب پایین
        multiplier = round(random.uniform(min_multiplier, 2.5), 1)
    elif random.random() < 0.65:  # 30% شانس ضریب متوسط
        multiplier = round(random.uniform(2.5, 4.5), 1)
    else:  # 35% شانس ضریب بالا
        multiplier = round(random.uniform(4.5, max_multiplier), 1)

    multiplier = min(multiplier, max_multiplier)

    # شانس برد بر اساس ضریب (والیبال شانس برد بالاتری دارد)
    if multiplier <= 2:
        win_chance = 0.70
    elif multiplier <= 4:
        win_chance = 0.55
    elif multiplier <= 6:
        win_chance = 0.40
    else:
        win_chance = 0.25

    is_win = random.random() < win_chance

    # تعداد ست‌های والیبال (شانسی)
    sets = f"{randint(0, 3)} - {randint(0, 3)}"

    win_amount = 0

    if is_win:
        win_amount = int(bet_amount * multiplier)
        user_data['meow_points'] = user_points + win_amount
        user_data['last_volleyball'] = current_time
        user_data['volleyball_wins'] = user_data.get('volleyball_wins', 0) + 1
        user_data['volleyball_total'] = user_data.get('volleyball_total', 0) + 1
        user_data['volleyball_total_won'] = user_data.get('volleyball_total_won', 0) + win_amount

        db.set_key(sender_id, user_data)

        bot.sendMessage(
            chat_id,
            f"🏐 بازی والیبال!\n\n"
            f"{random.choice(WIN_MESSAGES)}\n"
            f"📊 نتیجه ست‌ها: {sets}\n"
            f"💰 مبلغ شرط: {bet_amount:,} پوینت\n"
            f"🎯 ضریب: {multiplier}x\n"
            f"🏆 برد شما: {win_amount:,} پوینت\n"
            f"📊 موجودی جدید: {user_data['meow_points']:,} پوینت",
            reply_to_message_id=message_id
        )
    else:
        user_data['meow_points'] = user_points - bet_amount
        user_data['last_volleyball'] = current_time
        user_data['volleyball_losses'] = user_data.get('volleyball_losses', 0) + 1
        user_data['volleyball_total'] = user_data.get('volleyball_total', 0) + 1

        db.set_key(sender_id, user_data)

        bot.sendMessage(
            chat_id,
            f"🏐 بازی والیبال!\n\n"
            f"{random.choice(LOSS_MESSAGES)}\n"
            f"📊 نتیجه ست‌ها: {sets}\n"
            f"💰 مبلغ شرط: {bet_amount:,} پوینت\n"
            f"🎯 ضریب: {multiplier}x\n"
            f"📊 موجودی جدید: {user_data['meow_points']:,} پوینت",
            reply_to_message_id=message_id
        )

    # ثبت تاریخچه والیبال
    volleyball_history = db.get_key("volleyball_history", [])
    volleyball_history.append({
        'user_id': sender_id,
        'bet': bet_amount,
        'multiplier': multiplier,
        'result': 'win' if is_win else 'loss',
        'win_amount': win_amount if is_win else 0,
        'sets': sets,
        'time': current_time
    })
    if len(volleyball_history) > 200:
        volleyball_history = volleyball_history[-200:]
    db.set_key("volleyball_history", volleyball_history)

    return True
