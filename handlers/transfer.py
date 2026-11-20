# handlers/transfer.py
"""هندلر انتقال پوینت بین کاربران (pay)"""

import time

from config import PAY_MIN_USER_LEVEL

from core.db_instance import db
from core.helpers import check_user_registered, get_user_display_name
from core.roles import get_user_role,VALID_ROLES


def handle_pay(text, message, sender_id, message_id, chat_id, bot) -> bool:
    text_parts = text.split()
    if not text_parts[0].lower() == "pay":
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

    if user_level < PAY_MIN_USER_LEVEL:
        bot.sendMessage(
            chat_id,
            f"🔒 برای شرطبندی باید حداقل سطح {PAY_MIN_USER_LEVEL} باشی!\n"
            f"⭐️ سطح فعلی تو : {user_level}",
            reply_to_message_id=message_id
        )
        return True

    # بررسی اینکه پیام ریپلای شده باشد
    reply_to_message_id = message.get('reply_to_message_id', None)
    if not reply_to_message_id:
        bot.sendMessage(
            chat_id,
            "❌ برای انتقال پوینت باید روی پیام کاربر ریپلای کنی!\n"
            "مثال: /pay 100 (روی پیام کاربر ریپلای کن)",
            reply_to_message_id=message_id
        )
        return True

    if len(text_parts) < 2:
        bot.sendMessage(
            chat_id,
            "❌ مقدار پوینت را وارد کن!\n"
            "مثال: /pay 100",
            reply_to_message_id=message_id
        )
        return True

    try:
        point_amount = int(text_parts[1])
    except ValueError:
        bot.sendMessage(
            chat_id,
            "❌ مقدار وارد شده معتبر نیست! لطفاً یک عدد وارد کن.",
            reply_to_message_id=message_id
        )
        return True
    
    user_role = get_user_role(sender_id)
    
    if user_role == VALID_ROLES[2]:
        maximum_limit = 500000
    elif user_role == VALID_ROLES[3]:
        maximum_limit = 10000000000000000
    else:
        maximum_limit = 100000

    # بررسی محدوده پوینت
    if point_amount < 10 or point_amount > maximum_limit:
        bot.sendMessage(
            chat_id,
            f"❌ مقدار پوینت باید بین 10 تا {maximum_limit} باشد!",
            reply_to_message_id=message_id
        )
        return True

    # دریافت اطلاعات کاربر فرستنده
    user_data = db.get_key(sender_id, {})
    if not user_data:
        bot.sendMessage(
            chat_id,
            "❌ شما در دیتابیس ثبت نام نشده‌اید! لطفاً ربات را در پیوی استارت کنید.",
            reply_to_message_id=message_id
        )
        return True

    user_points = user_data.get('meow_points', 0)

    # بررسی موجودی کاربر
    if point_amount > user_points:
        bot.sendMessage(
            chat_id,
            f"❌ پوینت کافی نداری!\n"
            f"💰 پوینت شما: {user_points:,}\n"
            f"📤 پوینت مورد نیاز: {point_amount:,}",
            reply_to_message_id=message_id
        )
        return True

    # دریافت پیام ریپلای شده
    try:
        replied_message = bot.getMessage(chat_id + reply_to_message_id)
        if not replied_message:
            bot.sendMessage(
                chat_id,
                "❌ پیام مورد نظر پیدا نشد!",
                reply_to_message_id=message_id
            )
            return True
    except Exception:
        bot.sendMessage(
            chat_id,
            "❌ خطا در دریافت پیام ریپلای شده!",
            reply_to_message_id=message_id
        )
        return True

    # دریافت اطلاعات کاربر هدف
    target_id = replied_message.get('sender_id')
    if not target_id:
        bot.sendMessage(
            chat_id,
            "❌ شناسه کاربر هدف پیدا نشد!",
            reply_to_message_id=message_id
        )
        return True

    # بررسی اینکه کاربر خودش رو ریپلای نکرده باشد
    if target_id == sender_id:
        bot.sendMessage(
            chat_id,
            "❌ نمی‌تونی به خودت پوینت انتقال بدی!",
            reply_to_message_id=message_id
        )
        return True

    # دریافت اطلاعات کاربر هدف
    target_data = db.get_key(target_id, {})
    if not target_data:
        bot.sendMessage(
            chat_id,
            "❌ کاربر هدف در دیتابیس ثبت نام نشده است!",
            reply_to_message_id=message_id
        )
        return True

    # دریافت نام نمایشی کاربر هدف
    target_name = get_user_display_name(bot, target_id)

    # انجام انتقال پوینت
    target_data['meow_points'] = target_data.get('meow_points', 0) + point_amount
    user_data['meow_points'] = user_data.get('meow_points', 0) - point_amount

    # ذخیره در دیتابیس
    db.set_key(target_id, target_data)
    db.set_key(sender_id, user_data)

    # ثبت تاریخچه انتقال (اختیاری)
    transfer_history = db.get_key("transfer_history", [])
    transfer_history.append({
        'from': sender_id,
        'to': target_id,
        'amount': point_amount,
        'time': time.time()
    })
    # نگهداری فقط 100 تاریخچه آخر
    if len(transfer_history) > 100:
        transfer_history = transfer_history[-100:]
    db.set_key("transfer_history", transfer_history)

    # ارسال پیام موفقیت به فرستنده
    bot.sendMessage(
        chat_id,
        f"✅ انتقال پوینت با موفقیت انجام شد!\n\n"
        f"📤 به کاربر: {target_name}\n"
        f"💰 مبلغ: {point_amount:,} پوینت\n"
        f"📊 موجودی شما: {user_data['meow_points']:,} پوینت",
        reply_to_message_id=message_id
    )

    target_chat_id = target_data.get('chat_id')
    if target_chat_id:
        try:
            sender_name = get_user_display_name(bot, sender_id)
            bot.sendMessage(
                target_chat_id,
                f"🎉 شما {point_amount:,} پوینت از {sender_name} دریافت کردید!\n"
                f"💰 موجودی جدید: {target_data['meow_points']:,} پوینت"
            )
        except Exception:
            pass

    return True

