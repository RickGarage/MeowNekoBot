# handlers/games/basketball.py
"""بازی شرط‌بندی بسکتبال"""

import time
import random
from random import randint

from config import GAMELS_MIN_USER_LEVEL

from core.db_instance import db
from core.helpers import check_user_registered, format_time
from core.roles import get_user_role,VALID_ROLES

WIN_MESSAGES = [
    "🏀 شوت سه امتیازی! برد!",
    "🌟 سوپراستار بسکتبال!",
    "🔥 دانک! برد عالی!",
    "💪 تیمت برنده شد!",
    "🎯 شوت دقیق! گل کردی!"
]

LOSS_MESSAGES = [
    "😢 توپ به تیر خورد! باختی!",
    "💔 تیم حریف بهتر بود!",
    "😅 دفعه بعد میبری!",
    "🤷‍♂️ روزت نبود!",
    "🏀 باخت نزدیک! بازم تلاش کن!"
]


def handle_basketball(text, sender_id, message_id, chat_id, bot) -> bool:
    if not (text.lower().startswith("basketball") or text.lower().startswith("بسکتبال")):
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

    user_level = user_data.get('meow_level', 1)

    if user_level < GAMELS_MIN_USER_LEVEL:
        bot.sendMessage(
            chat_id,
            f"🔒 برای شرطبندی باید حداقل سطح {GAMELS_MIN_USER_LEVEL} باشی!\n"
            f"⭐️ سطح فعلی تو : {user_level}",
            reply_to_message_id=message_id
        )
        return True
    

    # بررسی کول‌داون (2 دقیقه = 120 ثانیه)
    last_basketball = user_data.get('last_basketball', 0)
    current_time = time.time()
    
    user_role = get_user_role(sender_id)
    
    if user_role == VALID_ROLES[2]:
        cooldown_seconds = 30
    elif user_role == VALID_ROLES[3]:
        cooldown_seconds = 0
    else:
        cooldown_seconds = 120

    if current_time - last_basketball < cooldown_seconds:
        remaining = int(cooldown_seconds - (current_time - last_basketball))
        formatted_time = format_time(remaining)
        bot.sendMessage(
            chat_id,
            f"🏀 هنوز زمان بسکتبال تموم نشده!\n"
            f"⏳ باید {formatted_time} صبر کنی تا دوباره بتونی بازی کنی.",
            reply_to_message_id=message_id
        )
        return True

    # استخراج مقدار شرط
    text_parts = text.split()
    if len(text_parts) < 2:
        bot.sendMessage(
            chat_id,
            "🏀 برای بازی بسکتبال باید مقدار پوینت رو وارد کنی!\n"
            "مثال: basketball 100\n"
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

    # محاسبه ضریب بسکتبال (1.5 تا سطح کاربر * 0.8)
    max_multiplier = min(user_level * 0.8, 8)  # حداکثر 8
    min_multiplier = 1.5

    # شانس ضریب‌ها
    if random.random() < 0.3:  # 30% شانس ضریب پایین
        multiplier = round(random.uniform(min_multiplier, 3), 1)
    elif random.random() < 0.6:  # 30% شانس ضریب متوسط
        multiplier = round(random.uniform(3, 5), 1)
    else:  # 40% شانس ضریب بالا
        multiplier = round(random.uniform(5, max_multiplier), 1)

    multiplier = min(multiplier, max_multiplier)

    # شانس برد بر اساس ضریب (هرچه ضریب بالاتر، شانس کمتر)
    if multiplier <= 2:
        win_chance = 0.65
    elif multiplier <= 4:
        win_chance = 0.50
    elif multiplier <= 6:
        win_chance = 0.35
    else:
        win_chance = 0.20

    is_win = random.random() < win_chance

    # تعداد امتیازهای بسکتبال (شانسی)
    basketball_score = randint(60, 120)

    win_amount = 0

    if is_win:
        win_amount = int(bet_amount * multiplier)
        user_data['meow_points'] = user_points + win_amount
        user_data['last_basketball'] = current_time
        user_data['basketball_wins'] = user_data.get('basketball_wins', 0) + 1
        user_data['basketball_total'] = user_data.get('basketball_total', 0) + 1
        user_data['basketball_total_won'] = user_data.get('basketball_total_won', 0) + win_amount

        db.set_key(sender_id, user_data)

        bot.sendMessage(
            chat_id,
            f"🏀 بازی بسکتبال!\n\n"
            f"{random.choice(WIN_MESSAGES)}\n"
            f"📊 امتیاز بازی: {basketball_score}\n"
            f"💰 مبلغ شرط: {bet_amount:,} پوینت\n"
            f"🎯 ضریب: {multiplier}x\n"
            f"🏆 برد شما: {win_amount:,} پوینت\n"
            f"📊 موجودی جدید: {user_data['meow_points']:,} پوینت",
            reply_to_message_id=message_id
        )
    else:
        user_data['meow_points'] = user_points - bet_amount
        user_data['last_basketball'] = current_time
        user_data['basketball_losses'] = user_data.get('basketball_losses', 0) + 1
        user_data['basketball_total'] = user_data.get('basketball_total', 0) + 1

        db.set_key(sender_id, user_data)

        bot.sendMessage(
            chat_id,
            f"🏀 بازی بسکتبال!\n\n"
            f"{random.choice(LOSS_MESSAGES)}\n"
            f"📊 امتیاز بازی: {basketball_score}\n"
            f"💰 مبلغ شرط: {bet_amount:,} پوینت\n"
            f"🎯 ضریب: {multiplier}x\n"
            f"📊 موجودی جدید: {user_data['meow_points']:,} پوینت",
            reply_to_message_id=message_id
        )

    # ثبت تاریخچه بسکتبال
    basketball_history = db.get_key("basketball_history", [])
    basketball_history.append({
        'user_id': sender_id,
        'bet': bet_amount,
        'multiplier': multiplier,
        'result': 'win' if is_win else 'loss',
        'win_amount': win_amount if is_win else 0,
        'score': basketball_score,
        'time': current_time
    })
    if len(basketball_history) > 200:
        basketball_history = basketball_history[-200:]
    db.set_key("basketball_history", basketball_history)

    return True
