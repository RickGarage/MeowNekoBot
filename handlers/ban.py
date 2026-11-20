# handlers/ban.py
"""هندلر زندان میویی: پرداخت جریمه و نمایش وضعیت"""

from core.db_instance import db
from core.antispam import is_user_banned, get_spam_ban_time, calculate_fine, user_messages
from core.helpers import format_time

PAY_FINE_KEYWORDS = ["پرداخت جریمه", "pay fine", "جریمه", "fine"]
BAN_STATUS_KEYWORDS = ["زندان", "ban status", "وضعیت زندان", "محرومیت"]


def handle_pay_fine(text, sender_id, chat_id, message_id, bot) -> bool:
    """پرداخت جریمه برای کاربر زندانی. فقط زمانی صدا زده می‌شود که کاربر بن شده باشد."""
    if text.lower() not in PAY_FINE_KEYWORDS:
        return False

    # بررسی اینکه کاربر زندانی است
    if not is_user_banned(sender_id):
        bot.sendMessage(
            chat_id,
            "✅ شما در زندان میویی نیستید! نیازی به پرداخت جریمه ندارید.",
            reply_to_message_id=message_id
        )
        return True

    # دریافت اطلاعات کاربر
    user_data = db.get_key(sender_id, {})
    remaining = get_spam_ban_time(sender_id)

    # محاسبه جریمه
    fine_amount = calculate_fine(remaining)

    # بررسی موجودی کاربر
    user_points = user_data.get('meow_points', 0)

    if user_points < fine_amount:
        bot.sendMessage(
            chat_id,
            f"🚫 پوینت کافی برای پرداخت جریمه نداری!\n\n"
            f"⏳ زمان باقی‌مانده: {format_time(remaining)}\n"
            f"💰 جریمه مورد نیاز: {fine_amount:,} پوینت\n"
            f"📊 موجودی شما: {user_points:,} پوینت\n"
            f"❌ {fine_amount - user_points:,} پوینت دیگر نیاز داری!",
            reply_to_message_id=message_id
        )
        return True

    # پرداخت جریمه و آزادی
    user_data['meow_points'] = user_points - fine_amount
    user_data['spam_ban_until'] = 0  # حذف محرومیت
    user_data['fine_paid'] = user_data.get('fine_paid', 0) + 1
    user_data['total_fine_paid'] = user_data.get('total_fine_paid', 0) + fine_amount

    db.set_key(sender_id, user_data)

    # پاک کردن تاریخچه پیام‌های کاربر
    if sender_id in user_messages:
        user_messages[sender_id] = []

    bot.sendMessage(
        chat_id,
        f"✅ جریمه پرداخت شد و شما از زندان میویی آزاد شدید! 😸\n\n"
        f"💰 مبلغ جریمه: {fine_amount:,} پوینت\n"
        f"📊 موجودی جدید: {user_data['meow_points']:,} پوینت\n"
        f"📈 تعداد دفعات پرداخت جریمه: {user_data['fine_paid']}\n"
        f"💳 کل جریمه پرداختی: {user_data['total_fine_paid']:,} پوینت\n\n"
        f"🎉 از این به بعد بیشتر مراقب باش!",
        reply_to_message_id=message_id
    )
    return True


def handle_ban_status(text, sender_id, chat_id, message_id, bot) -> bool:
    """نمایش وضعیت زندان کاربر"""
    if text.lower() not in BAN_STATUS_KEYWORDS:
        return False

    if is_user_banned(sender_id):
        remaining = get_spam_ban_time(sender_id)
        fine_amount = calculate_fine(remaining)

        bot.sendMessage(
            chat_id,
            f"🚫 شما در زندان میویی هستید!\n\n"
            f"⏳ زمان باقی‌مانده: {format_time(remaining)}\n"
            f"💰 جریمه پرداخت: {fine_amount:,} پوینت\n\n"
            f"📋 برای پرداخت جریمه و آزادی:\n"
            f"دستور: `پرداخت جریمه` یا `pay fine`",
            reply_to_message_id=message_id
        )
    else:
        user_data = db.get_key(sender_id, {})
        bot.sendMessage(
            chat_id,
            f"✅ شما در زندان میویی نیستید! 😸\n\n"
            f"📊 تعداد دفعات محرومیت: {user_data.get('spam_count', 0)}\n"
            f"💰 کل جریمه پرداختی: {user_data.get('total_fine_paid', 0):,} پوینت",
            reply_to_message_id=message_id
        )
    return True
