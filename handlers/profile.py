# handlers/profile.py
"""هندلر پروفایل کاربر"""

from core.db_instance import db
from core.helpers import cur, get_user_display_name
from core.levels import get_level_bar
from core.ranking import get_rotbe_meow_points, get_rotbe_meow_count

PROFILE_KEYWORDS = ["میو هام", "mymeows", "my meows", "پروفایل", "profile","میوهام"]


def handle_profile(text, chat_type, sender_id, message_id, chat_id, bot) -> bool:
    if text.lower() not in PROFILE_KEYWORDS:
        return False

    if not cur(chat_type, sender_id, message_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {
        'meow_points': 0,
        'meow_timeout': 0,
        'meow_count': 0,
        'meow_level': 1,
        'meow_xp': 0,
        'total_meows': 0
    })

    meow_points = user_data.get('meow_points', 0)
    meow_count = user_data.get('meow_count', 0)
    meow_level = user_data.get('meow_level', 1)
    meow_xp = user_data.get('meow_xp', 0)

    # دریافت رتبه‌ها
    points_rank = get_rotbe_meow_points(sender_id)
    count_rank = get_rotbe_meow_count(sender_id)

    # دریافت نوار پیشرفت
    level_bar = get_level_bar(sender_id, meow_level, meow_xp)

    # دریافت نام نمایشی کاربر (با استفاده از sender_id که همان user_id است)
    display_name = get_user_display_name(bot, sender_id)

    bot.sendMessage(
        chat_id,
        f"""
╮──「 🐱 پروفایل میویی 🐱 」

┐─ 👤 کاربر : {display_name}
‏┘─ 🪪 آیدی : {sender_id[:12]}...

┐─ 💰 میو پوینت ها : {meow_points:,} 🪙
┘─ 🎖️ رتبه پوینت : #{points_rank}
┐─ 🐾 میو میو ها : {meow_count:,}
┘─ 🎖️ رتبه میو : #{count_rank}

╯─ {level_bar}
""", reply_to_message_id=message_id
    )
    return True

PROFILESH_KEYWORDS = ["میو هاش", "پروفایلش", "میوهاش"]


def handle_profile_reply(text, message, chat_type, sender_id, message_id, chat_id, bot) -> bool:
    # فقط اگر متن با کلمات کلیدی پروفایل مطابقت داشته باشد
    if text.lower() not in PROFILESH_KEYWORDS:
        return False

    # بررسی اینکه پیام ریپلای شده باشد
    reply_to_message_id = message.get('reply_to_message_id')
    if not reply_to_message_id:
        return False  # اگر ریپلای نبود، هندلر بعدی (پروفایل خود کاربر) اجرا شود

    if not cur(chat_type, sender_id, message_id, chat_id, bot):
        return True

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

    target_id = replied_message.get('sender_id')
    if not target_id:
        bot.sendMessage(
            chat_id,
            "❌ شناسه کاربر هدف پیدا نشد!",
            reply_to_message_id=message_id
        )
        return True

    target_data = db.get_key(target_id, {})
    if not target_data:
        bot.sendMessage(
            chat_id,
            "❌ کاربر هدف در دیتابیس ثبت نام نشده است!",
            reply_to_message_id=message_id
        )
        return True

    # استخراج اطلاعات
    meow_points = target_data.get('meow_points', 0)
    meow_count = target_data.get('meow_count', 0)
    meow_level = target_data.get('meow_level', 1)
    meow_xp = target_data.get('meow_xp', 0)

    # رتبه‌ها
    points_rank = get_rotbe_meow_points(target_id)
    count_rank = get_rotbe_meow_count(target_id)

    # نوار پیشرفت
    level_bar = get_level_bar(target_id, meow_level, meow_xp)

    # نام نمایشی کاربر هدف
    display_name = get_user_display_name(bot, target_id)

    bot.sendMessage(
        chat_id,
        f"""
╮──「 🐱 پروفایل میویی {display_name} 🐱 」

┐─ 👤 کاربر : {display_name}
‏┘─ 🪪 آیدی : {target_id[:12]}...

┐─ 💰 میو پوینت ها : {meow_points:,} 🪙
┘─ 🎖️ رتبه پوینت : #{points_rank}
┐─ 🐾 میو میو ها : {meow_count:,}
┘─ 🎖️ رتبه میو : #{count_rank}

╯─ {level_bar}
""", reply_to_message_id=message_id
    )
    return True