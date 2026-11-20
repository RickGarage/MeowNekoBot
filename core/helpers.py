# core/helpers.py
"""توابع کمکی عمومی"""

from rubik import ChatModel
from core.db_instance import db
from core.antispam import is_user_banned, get_spam_ban_time


def format_time(seconds):
    """تبدیل ثانیه به فرمت دقیقه:ثانیه"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"


def get_user_display_name(bot, user_id):
    """دریافت نام نمایشی کاربر با مدیریت خطا"""
    try:
        user_data = db.get_key(user_id, {})
        chat_id = user_data.get('chat_id', user_id[:8] + '...')
        if not user_data.get('chat_data'):
            chat_info = bot.getChat(chat_id)
            user_data['chat_data'] = chat_info.to_dict()
            db.set_key(user_id, user_data)
        else:
            chat_info = ChatModel(user_data.get('chat_data'))
        if chat_info:
            return chat_info.get_display_name()
    except Exception:
        pass
    return user_id[:8] + '...'


def check_user_registered(sender_id, chat_id, bot):
    """بررسی اینکه کاربر ثبت نام کرده و چت آیدی دارد"""
    user_data = db.get_key(sender_id, {})

    # اگر کاربر داده‌ای ندارد یا chat_id ندارد
    if not user_data or user_data.get('chat_id') is None:
        # ارسال پیام به کاربر برای رفتن به پیوی
        try:
            bot.sendMessage(
                chat_id,
                f"🐱 برای استفاده از ربات میویی، لطفاً ابتدا ربات را در پیوی استارت کنید:\n\n"
                f"👤 @MeowNekoBot\n"
                f"یا روی لینک زیر کلیک کنید:\n"
                f"https://rubika.ir/MeowNekoBot"
            )
        except Exception:
            pass
        return False

    return True


def cur(chat_type, sender_id, message_id, chat_id, bot):
    """بررسی ثبت‌نام و وضعیت زندان کاربر قبل از اجرای دستورات گروهی"""
    if chat_type == "Group" or chat_type == "SuperGroup":
        # بررسی ثبت نام
        if not check_user_registered(sender_id, chat_id, bot):
            return False

        # بررسی زندان
        if is_user_banned(sender_id):
            remaining = get_spam_ban_time(sender_id)
            minutes = remaining // 60
            seconds = remaining % 60
            bot.sendMessage(
                chat_id,
                f"🚫 شما در زندان میویی هستید!\n"
                f"⏳ زمان باقی‌مانده: {minutes} دقیقه و {seconds} ثانیه",
                reply_to_message_id=message_id
            )
            return False

        return True
    return True
