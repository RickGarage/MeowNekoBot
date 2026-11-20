# handlers/invite.py
"""هندلرهای سیستم دعوت میویی"""

from core.db_instance import db
from core.helpers import check_user_registered, get_user_display_name
from core.referral import (
    generate_invite_code,
    use_referral_code,
    get_invite_stats,
    get_referral_leaderboard
)
from config import REFERRAL_MIN_LEVEL, REFERRAL_REWARD_POINTS


def handle_generate_invite(text, sender_id, message_id, chat_id, bot) -> bool:
    """ساخت کد دعوت - دستور: ساخت کد دعوت"""
    if text.strip() not in ["ساخت کد دعوت", "invite code", "ساخت کد"]:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    code = generate_invite_code(sender_id)
    if not code:
        user_level = db.get_key(sender_id, {}).get('meow_level', 1)
        bot.sendMessage(
            chat_id,
            f"❌ برای ساخت کد دعوت باید سطح {REFERRAL_MIN_LEVEL} یا بالاتر باشی!\n"
            f"⭐ سطح فعلی تو: {user_level}",
            reply_to_message_id=message_id
        )
        return True

    stats = get_invite_stats(sender_id)
    bot.sendMessage(
        chat_id,
        f"🎁 کد دعوت شما:\n"
        f"┘─ `{code}`\n\n"
        f"برای دعوت از دوستان، این کد را به آنها بده.\n"
        f"هر کاربر جدید با این کد ثبت‌نام کند، {REFERRAL_REWARD_POINTS:,} میو پوینت به شما پاداش داده می‌شود.\n\n"
        f"📊 تعداد دعوت‌های موفق: {stats['total_invites']}",
        reply_to_message_id=message_id
    )
    return True


def handle_use_invite(text, sender_id, message_id, chat_id, bot) -> bool:
    """ثبت کد دعوت - دستور: ثبت کد دعوت [کد]"""
    if not text.lower().startswith("ثبت کد دعوت ") and not text.lower().startswith("use invite "):
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    parts = text.split(maxsplit=2)
    if len(parts) < 3:
        bot.sendMessage(
            chat_id,
            "❌ کد دعوت را وارد کن!\nمثال: ثبت کد دعوت ABC123",
            reply_to_message_id=message_id
        )
        return True

    code = parts[2].strip().upper()
    success, msg = use_referral_code(sender_id, code)
    bot.sendMessage(chat_id, msg, reply_to_message_id=message_id)
    return True


def handle_my_invite(text, sender_id, message_id, chat_id, bot) -> bool:
    """نمایش کد دعوت و آمار - دستور: کد دعوت من"""
    if text.strip() not in ["کد دعوت من", "my invite", "invite stats"]:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    stats = get_invite_stats(sender_id)
    if stats['code']:
        msg = f"🎁 کد دعوت شما: `{stats['code']}`\n"
        msg += f"📊 تعداد دعوت‌های موفق: {stats['total_invites']}\n\n"
        msg += f"با هر دعوت، {REFERRAL_REWARD_POINTS:,} میو پوینت پاداش می‌گیری!"
    else:
        msg = f"❌ شما هنوز کد دعوت نساخته‌اید.\n"
        if stats['can_generate']:
            msg += "برای ساخت کد، دستور «ساخت کد دعوت» را بفرست."
        else:
            msg += f"برای ساخت کد باید سطح {REFERRAL_MIN_LEVEL} یا بالاتر باشی."

    bot.sendMessage(chat_id, msg, reply_to_message_id=message_id)
    return True


def handle_invite_leaderboard(text, sender_id, message_id, chat_id, bot) -> bool:
    """لیدربرد دعوت‌ها - دستور: لیدربرد دعوت"""
    if text.strip() not in ["لیدربرد دعوت", "invite leaderboard", "دعوت لیدربرد"]:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    top = get_referral_leaderboard(10)
    if not top:
        bot.sendMessage(chat_id, "📊 هنوز کسی دعوتی انجام نداده!", reply_to_message_id=message_id)
        return True

    msg = "🏆 **لیدربرد دعوت‌ها**\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for idx, (uid, count) in enumerate(top, 1):
        medal = medals[idx-1] if idx <= 3 else f"#{idx}"
        name = get_user_display_name(bot, uid)
        msg += f"{medal} {name} — {count} دعوت\n"

    bot.sendMessage(chat_id, msg, reply_to_message_id=message_id)
    return True