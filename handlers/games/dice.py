# handlers/games/dice.py
"""بازی تاس"""

import time
import random
from random import randint

from config import GAMELS_MIN_USER_LEVEL

from core.db_instance import db
from core.helpers import check_user_registered, format_time
from core.roles import get_user_role,VALID_ROLES


WIN_MESSAGES = [
    "🎲 تاس ۶ آوردی! برد بزرگ!",
    "🌟 شانس با تو بود! تاس خوبی اومد!",
    "🔥 عالی! تاس ۵ و ۶!",
    "💪 استاد تاس! برد کردی!"
]

DRAW_MESSAGES = [
    "🎲 مساوی شد! پوینتت برگشت!",
    "😐 تاس ۳ و ۴! نه برد نه باخت!",
    "🤷‍♂️ تساوی! دوباره تلاش کن!",
    "🔄 پوینتت سالم موند!"
]

LOSS_MESSAGES = [
    "😢 تاس ۱ و ۲! باختی!",
    "💔 بدشانسی! تاس کوچیک اومد!",
    "😅 دفعه بعد بهتر شانس بیار!",
    "🤦‍♂️ بازم تلاش کن!"
]


def handle_dice(text, sender_id, message_id, chat_id, bot) -> bool:
    if not (text.lower().startswith("dice") or text.lower().startswith("تاس")):
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

    # بررسی کول‌داون (1 دقیقه = 60 ثانیه)
    last_dice = user_data.get('last_dice', 0)
    current_time = time.time()
    user_role = get_user_role(sender_id)
    
    if user_role == VALID_ROLES[2]:
        cooldown_seconds = 30
    elif user_role == VALID_ROLES[3]:
        cooldown_seconds = 0
    else:
        cooldown_seconds = 60

    if current_time - last_dice < cooldown_seconds:
        remaining = int(cooldown_seconds - (current_time - last_dice))
        formatted_time = format_time(remaining)
        bot.sendMessage(
            chat_id,
            f"🎲 هنوز زمان تاس انداختن تموم نشده!\n"
            f"⏳ باید {formatted_time} صبر کنی تا دوباره بتونی تاس بندازی.",
            reply_to_message_id=message_id
        )
        return True

    # استخراج مقدار شرط
    text_parts = text.split()
    if len(text_parts) < 2:
        bot.sendMessage(
            chat_id,
            "🎲 برای تاس انداختن باید مقدار پوینت رو وارد کنی!\n"
            "مثال: dice 50\n"
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

    # انداختن تاس (اعداد 1 تا 6)
    dice_number = randint(1, 6)

    # تعیین نتیجه بر اساس عدد تاس
    # اعداد 1-2: باخت, 3-4: تساوی (برگشت پوینت), 5-6: برد
    if dice_number >= 5:
        # برد (ضریب 2x)
        win_amount = bet_amount * 2
        user_data['meow_points'] = user_points + win_amount
        user_data['last_dice'] = current_time
        user_data['dice_wins'] = user_data.get('dice_wins', 0) + 1
        user_data['dice_total'] = user_data.get('dice_total', 0) + 1
        user_data['dice_total_won'] = user_data.get('dice_total_won', 0) + win_amount

        db.set_key(sender_id, user_data)

        bot.sendMessage(
            chat_id,
            f"🎲 تاس انداختی!\n\n"
            f"{random.choice(WIN_MESSAGES)}\n"
            f"🎯 عدد تاس: {dice_number}\n"
            f"💰 مبلغ شرط: {bet_amount:,} پوینت\n"
            f"🏆 برد شما: {win_amount:,} پوینت\n"
            f"📊 موجودی جدید: {user_data['meow_points']:,} پوینت",
            reply_to_message_id=message_id
        )

    elif dice_number >= 3:
        # تساوی (برگشت پوینت)
        user_data['last_dice'] = current_time
        user_data['dice_draws'] = user_data.get('dice_draws', 0) + 1
        user_data['dice_total'] = user_data.get('dice_total', 0) + 1

        db.set_key(sender_id, user_data)

        bot.sendMessage(
            chat_id,
            f"🎲 تاس انداختی!\n\n"
            f"{random.choice(DRAW_MESSAGES)}\n"
            f"🎯 عدد تاس: {dice_number}\n"
            f"💰 مبلغ شرط: {bet_amount:,} پوینت\n"
            f"📊 موجودی شما: {user_data['meow_points']:,} پوینت",
            reply_to_message_id=message_id
        )

    else:
        # باخت (اعداد 1-2)
        user_data['meow_points'] = user_points - bet_amount
        user_data['last_dice'] = current_time
        user_data['dice_losses'] = user_data.get('dice_losses', 0) + 1
        user_data['dice_total'] = user_data.get('dice_total', 0) + 1

        db.set_key(sender_id, user_data)

        bot.sendMessage(
            chat_id,
            f"🎲 تاس انداختی!\n\n"
            f"{random.choice(LOSS_MESSAGES)}\n"
            f"🎯 عدد تاس: {dice_number}\n"
            f"💰 مبلغ شرط: {bet_amount:,} پوینت\n"
            f"📊 موجودی جدید: {user_data['meow_points']:,} پوینت",
            reply_to_message_id=message_id
        )

    # ثبت تاریخچه تاس
    dice_history = db.get_key("dice_history", [])
    dice_history.append({
        'user_id': sender_id,
        'bet': bet_amount,
        'dice': dice_number,
        'result': 'win' if dice_number >= 5 else 'draw' if dice_number >= 3 else 'loss',
        'time': current_time
    })
    if len(dice_history) > 200:
        dice_history = dice_history[-200:]
    db.set_key("dice_history", dice_history)

    return True
