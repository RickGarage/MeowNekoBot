# handlers/leaderboard.py
"""هندلرهای لیدربرد میو پوینت و میو میو"""

from core.helpers import cur, get_user_display_name
from core.ranking import get_top_users, get_rotbe_meow_points, get_rotbe_meow_count

TOP_POINTS_KEYWORDS = ["لیدربرد پوینت", "top points", "تاپ پوینت"]
TOP_MEOWS_KEYWORDS = ["لیدربرد میو", "top meows", "تاپ میو"]

MEDALS = ["🥇", "🥈", "🥉", "🎖", "🏅"]
TITLES = ["پادشاه پیشی ها", "قهرمان پیشی ها", "وزیر پیشی ها", "پیشی برتر", "پیشی برتر"]


def handle_top_points(text, chat_type, sender_id, message_id, chat_id, bot) -> bool:
    if text.lower() not in TOP_POINTS_KEYWORDS:
        return False

    if not cur(chat_type, sender_id, message_id, chat_id, bot):
        return True

    top_users = get_top_users('points', 5)

    if not top_users:
        bot.sendMessage(chat_id, "هنوز کاربری در لیدربرد وجود ندارد!", reply_to_message_id=message_id)
        return True

    message = "🌍 لیدربرد جهانی میویی 🐱\n\n🪙 ثروتمند ترین پیشی‌ های کل دنیای میویی\n\n"

    for idx, (uid, user_points, data) in enumerate(top_users):
        # اطمینان از اینکه data دیکشنری است
        if not isinstance(data, dict):
            data = {}

        medal = MEDALS[idx] if idx < len(MEDALS) else f"#{idx+1}"
        title = TITLES[idx] if idx < len(TITLES) else "پیشی برتر"

        meow_count = data.get('meow_count', 0) if isinstance(data, dict) else 0
        display_name = get_user_display_name(bot, uid)

        message += f"{medal} {title} : {display_name} 🏆\n"
        message += f"┘─ 💰 میو پوینت ها : {user_points:,} 🪙\n"
        message += f"┘─ 🐾 میو میو ها : {meow_count:,} 🐈\n\n"

    # رتبه کاربر
    user_rank = get_rotbe_meow_points(sender_id)
    message += f"🎖️ رتبه جهانی شما : {user_rank}"

    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True


def handle_top_meows(text, chat_type, sender_id, message_id, chat_id, bot) -> bool:
    if text.lower() not in TOP_MEOWS_KEYWORDS:
        return False

    if not cur(chat_type, sender_id, message_id, chat_id, bot):
        return True

    top_users = get_top_users('count', 5)

    if not top_users:
        bot.sendMessage(chat_id, "هنوز کاربری در لیدربرد وجود ندارد!", reply_to_message_id=message_id)
        return True

    message = "🌍 لیدربرد جهانی میویی 🐱\n\n🐾 پر سر و صدا ترین پیشی‌ های کل دنیای میویی\n\n"

    for idx, (uid, count, data) in enumerate(top_users):
        medal = MEDALS[idx] if idx < len(MEDALS) else f"#{idx+1}"
        title = TITLES[idx] if idx < len(TITLES) else "پیشی برتر"

        user_points = data.get('meow_points', 0)
        display_name = get_user_display_name(bot, uid)

        message += f"{medal} {title} : {display_name} 🏆\n"
        message += f"┘─ 🐾 میو میو ها : {count:,} 🐈\n"
        message += f"┘─ 💰 میو پوینت ها : {user_points:,} 🪙\n\n"

    # رتبه کاربر
    user_rank = get_rotbe_meow_count(sender_id)
    message += f"🎖️ رتبه جهانی شما : {user_rank}"

    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True
