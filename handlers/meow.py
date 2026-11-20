"""هندلر دستور میو (مکانیزم اصلی کسب پوینت)"""

import time
from random import randint

from config import MEOW_KEYWORDS
from core.db_instance import db
from core.helpers import cur, format_time
from core.levels import (
    get_cooldown_for_level,
    get_points_range_for_level,
    update_user_level,
    get_level_config,
    get_xp_info,
)
from handlers.street_cats import try_spawn_street_cat


def handle_meow(text, chat_type, sender_id, message_id, chat_id, bot) -> bool:
    if text.lower() not in MEOW_KEYWORDS:
        return False

    if not cur(chat_type, sender_id, message_id, chat_id, bot):
        return True

    current_time = time.time()

    user_data = db.get_key(sender_id, {
        'meow_points': 0,
        'meow_timeout': 0,
        'meow_count': 0,
        'meow_level': 1,
        'meow_xp': 0,
        'total_meows': 0
    })

    last_time = user_data.get('meow_timeout', 0)
    time_diff = current_time - last_time

    level = user_data.get('meow_level', 1)
    cooldown_seconds = get_cooldown_for_level(level)

    if time_diff >= cooldown_seconds or last_time == 0:
        points_range = get_points_range_for_level(level)
        meow = randint(points_range[0], points_range[1])

        user_data['meow_points'] = user_data.get('meow_points', 0) + meow
        user_data['meow_timeout'] = current_time
        user_data['meow_count'] = user_data.get('meow_count', 0) + 1
        user_data['total_meows'] = user_data.get('total_meows', 0) + 1

        # بروزرسانی سطح و XP (افزایش XP به صورت مستقل)
        user_data = update_user_level(sender_id, user_data)

        # ذخیره در دیتابیس
        db.set_key(sender_id, user_data)

        # دریافت اطلاعات به‌روز شده
        user_meows = user_data.get('meow_points', 0)
        user_level = user_data.get('meow_level', 1)
        user_xp = user_data.get('meow_xp', 0)

        # دریافت اطلاعات XP مورد نیاز
        xp_info = get_xp_info(user_level)
        xp_needed = xp_info['xp_needed']

        # پیام موفقیت
        bonus_msg = ""
        if user_data.get('level_up', False):
            bonus = get_level_config(user_level)['bonus']
            bonus_msg = f"\n🎉 به سطح {user_level} ارتقا پیدا کردی! +{bonus:,} پوینت جایزه!"
            user_data['level_up'] = False
            db.set_key(sender_id, user_data)

        # ساخت پیام با نمایش XP
        msg = f"{meow} میو پوینت گرفتی 🐾\n"
        msg += f"💰 میو پوینت هات : {user_meows:,} 🪙\n"
        msg += f"⭐️ سطح : {user_level}\n"
        msg += f"📊 XP : {user_xp} / {xp_needed}\n"
        msg += f"⏳ بعد از {format_time(cooldown_seconds)} میتونی دوباره میو میو کنی"
        msg += bonus_msg

        bot.sendMessage(chat_id, msg, reply_to_message_id=message_id)

        # شانس ظاهر شدن یه پیشی خیابونی
        try_spawn_street_cat(chat_type, chat_id, bot)
    else:
        remaining = int(cooldown_seconds - time_diff)
        formatted_time = format_time(remaining)
        bot.sendMessage(
            chat_id,
            f"🐱 هنوز میوت نمیاد..\n⏳ باید {formatted_time} صبر کنی",
            reply_to_message_id=message_id
        )

    return True