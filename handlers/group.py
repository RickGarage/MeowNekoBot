# handlers/group.py
"""هندلر پیوستن به گروه (سرزمین میویی)، خروج از گروه، لیدربرد داخل سرزمین و آمار گروه"""

from core.db_instance import db

from config import JOINING_MIN_USER_LEVEL

from core.helpers import cur, get_user_display_name
from core.groups import join_group, get_group_top_users, get_group_rank, get_group_data, leave_group, get_group_stats

JOIN_GROUP_KEYWORDS = ["پیوستن به گروه", "پیوستن به سرزمین"]
LEAVE_GROUP_KEYWORDS = ["خروج از گروه", "خروج از سرزمین"]
GROUP_STATS_KEYWORDS = ["آمار گروه", "آمار سرزمین"]
LAND_POINTS_KEYWORDS = ["لیدربرد سرزمین پوینت", "لیدربرد سرزمین"]
LAND_MEOWS_KEYWORDS = ["لیدربرد سرزمین میو"]

MEDALS = ["🥇", "🥈", "🥉", "🎖", "🏅"]


def handle_join_group(text, chat_type, sender_id, message_id, chat_id, bot) -> bool:
    if text not in JOIN_GROUP_KEYWORDS:
        return False

    if chat_type not in ("Group", "SuperGroup"):
        bot.sendMessage(
            chat_id,
            "🏙 این دستور فقط داخل گروه‌ ها کار می‌کنه!",
            reply_to_message_id=message_id
        )
        return True

    if not cur(chat_type, sender_id, message_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})

    if not user_data:
            bot.sendMessage(
                chat_id,
                "❌ شما در دیتابیس ثبت نام نشده‌اید! لطفاً ربات را در پیوی استارت کنید.",
                reply_to_message_id=message_id
            )
            return True

    user_level = user_data.get('meow_level', 1)

    if user_level < JOINING_MIN_USER_LEVEL:
        bot.sendMessage(
            chat_id,
            f"🔒 برای پیوستن به سرزمین باید حداقل سطح {JOINING_MIN_USER_LEVEL} باشی!\n"
            f"⭐️ سطح فعلی تو : {user_level}",
            reply_to_message_id=message_id
        )
        return True

    success, status = join_group(sender_id, chat_id, bot)

    if not success:
        bot.sendMessage(chat_id, "❌ مشکلی پیش اومد، دوباره تلاش کن.", reply_to_message_id=message_id)
        return True

    group_data = get_group_data(chat_id)
    title = (group_data or {}).get('title') or "این سرزمین"

    if status == 'already_member':
        message = f"🐾 تو همین الانم ساکن سرزمین «{title}» هستی!"
    elif status == 'switched':
        message = f"🏙 با موفقیت به سرزمین «{title}» نقل مکان کردی! 🐾"
    else:
        message = f"🎉 خوش اومدی به سرزمین «{title}» 🐈\nحالا در لیدربرد سرزمینت شرکت می‌کنی!"

    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True


def handle_leave_group(text, chat_type, sender_id, message_id, chat_id, bot) -> bool:
    if text not in LEAVE_GROUP_KEYWORDS:
        return False

    if chat_type not in ("Group", "SuperGroup"):
        bot.sendMessage(
            chat_id,
            "🏙 این دستور فقط داخل گروه‌ ها کار می‌کنه!",
            reply_to_message_id=message_id
        )
        return True

    if not cur(chat_type, sender_id, message_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    current_group = user_data.get('group_id')

    if not current_group:
        bot.sendMessage(
            chat_id,
            "❌ شما عضو هیچ سرزمینی نیستی!",
            reply_to_message_id=message_id
        )
        return True

    if current_group != chat_id:
        bot.sendMessage(
            chat_id,
            "❌ شما عضو این سرزمین نیستی! برای خروج از سرزمین خودت به همان گروه برو.",
            reply_to_message_id=message_id
        )
        return True

    success = leave_group(sender_id, chat_id)
    if not success:
        bot.sendMessage(chat_id, "❌ خطا در خروج از گروه، دوباره تلاش کن.", reply_to_message_id=message_id)
        return True

    group_data = get_group_data(chat_id)
    title = (group_data or {}).get('title') or "این سرزمین"

    bot.sendMessage(
        chat_id,
        f"👋 شما با موفقیت از سرزمین «{title}» خارج شدید.\n"
        f"اگر دوباره بخوای عضو بشی، دوباره بگو «پیوستن به گروه».",
        reply_to_message_id=message_id
    )
    return True


def handle_group_stats(text, chat_type, sender_id, message_id, chat_id, bot) -> bool:
    if text not in GROUP_STATS_KEYWORDS:
        return False

    if chat_type not in ("Group", "SuperGroup"):
        bot.sendMessage(
            chat_id,
            "🏙 این آمار فقط داخل گروه‌ ها قابل مشاهده‌ ست!",
            reply_to_message_id=message_id
        )
        return True

    if not cur(chat_type, sender_id, message_id, chat_id, bot):
        return True

    group_data = get_group_data(chat_id)
    if not group_data:
        bot.sendMessage(
            chat_id,
            "📊 این گروه هنوز به عنوان یک سرزمین ثبت نشده!",
            reply_to_message_id=message_id
        )
        return True

    stats = get_group_stats(chat_id)
    title = group_data.get('title') or "سرزمین بدون نام"

    # دریافت نقش کاربر (برای نمایش در آمار)
    from core.roles import get_user_role, get_role_display_name
    user_role = get_user_role(sender_id)

    msg = f"🏙 **آمار سرزمین «{title}»**\n\n"
    msg += f"👥 تعداد ساکنان: {stats['member_count']:,}\n"
    msg += f"💰 مجموع پوینت‌ها: {stats['total_points']:,}\n"
    msg += f"🐾 مجموع میوها: {stats['total_meows']:,}\n"
    msg += f"📈 میانگین پوینت: {stats['avg_points']:,}\n"
    msg += f"📊 میانگین میو: {stats['avg_meows']:,}\n\n"
    msg += f"🎖️ نقش شما: {get_role_display_name(user_role)}"

    # اگر کاربر عضو این گروه است، رتبه‌اش را هم نشان بده
    user_data = db.get_key(sender_id, {})
    if user_data.get('group_id') == chat_id:
        points_rank = get_group_rank(chat_id, sender_id, 'points')
        meows_rank = get_group_rank(chat_id, sender_id, 'count')
        msg += f"\n\n📊 رتبه شما در این سرزمین:\n"
        msg += f"┘─ پوینت: #{points_rank}\n"
        msg += f"┘─ میو: #{meows_rank}"

    bot.sendMessage(chat_id, msg, reply_to_message_id=message_id)
    return True


def _build_land_leaderboard_message(chat_id, sender_id, bot, by, title_fa, unit_label, value_fmt):
    group_data = get_group_data(chat_id)
    land_title = (group_data or {}).get('title') or "سرزمین شما"

    top_users = get_group_top_users(chat_id, by, 5)

    if not top_users:
        return (
            f"🏙 لیدربرد سرزمین «{land_title}» 🐱\n\n"
            f"هنوز هیچ ساکنی رتبه‌ ای کسب نکرده! با گفتن «پیوستن به گروه» شروع کن."
        )

    message = f"🏙 لیدربرد سرزمین «{land_title}» 🐱\n\n{title_fa}\n\n"

    for idx, (uid, value, data) in enumerate(top_users):
        medal = MEDALS[idx] if idx < len(MEDALS) else f"#{idx+1}"
        display_name = get_user_display_name(bot, uid)
        message += f"{medal} {display_name}\n"
        message += f"┘─ {unit_label} : {value_fmt(value)}\n\n"

    user_rank = get_group_rank(chat_id, sender_id, by)
    message += f"🎖️ رتبه شما در این سرزمین : {user_rank}"

    return message


def handle_land_points_leaderboard(text, chat_type, sender_id, message_id, chat_id, bot) -> bool:
    if text not in LAND_POINTS_KEYWORDS:
        return False

    if chat_type not in ("Group", "SuperGroup"):
        bot.sendMessage(chat_id, "🏙 این لیدربرد فقط داخل گروه‌ ها قابل مشاهده‌ ست!", reply_to_message_id=message_id)
        return True

    if not cur(chat_type, sender_id, message_id, chat_id, bot):
        return True

    message = _build_land_leaderboard_message(
        chat_id, sender_id, bot, 'points',
        "🪙 ثروتمند ترین پیشی‌ های این سرزمین",
        "💰 میو پوینت",
        lambda v: f"{v:,} 🪙"
    )
    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True


def handle_land_meows_leaderboard(text, chat_type, sender_id, message_id, chat_id, bot) -> bool:
    if text not in LAND_MEOWS_KEYWORDS:
        return False

    if chat_type not in ("Group", "SuperGroup"):
        bot.sendMessage(chat_id, "🏙 این لیدربرد فقط داخل گروه‌ ها قابل مشاهده‌ ست!", reply_to_message_id=message_id)
        return True

    if not cur(chat_type, sender_id, message_id, chat_id, bot):
        return True

    message = _build_land_leaderboard_message(
        chat_id, sender_id, bot, 'count',
        "🐾 پر سر و صدا ترین پیشی‌ های این سرزمین",
        "🐾 میو میو",
        lambda v: f"{v:,} 🐈"
    )
    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True