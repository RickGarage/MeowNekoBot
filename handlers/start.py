# handlers/start.py
"""هندلر دستور /start"""

from config import START_MESSAGE
from core.db_instance import db


def handle_start(text, chat_type, sender_id, chat_id, message_id, bot) -> bool:
    """
    اگر در پیوی هستیم و دستور /start است، chat_id کاربر را ذخیره می‌کند.

    Returns:
        bool: True اگر پیام مدیریت شد
    """
    if chat_type == "Private" and text == "/start":
        # ذخیره یا بروزرسانی chat_id کاربر
        user_data = db.get_key(sender_id, {})
        user_data['chat_id'] = chat_id  # ذخیره chat_id
        db.set_key(sender_id, user_data)

        bot.sendMessage(chat_id, START_MESSAGE, reply_to_message_id=message_id)
        return True

    return False


def ensure_user_exists(sender_id, chat_id, chat_type):
    """اگر کاربر وجود نداشته باشد، رکورد اولیه او را ایجاد می‌کند"""
    if not sender_id:
        return

    user_data = db.get_key(sender_id, None)
    if user_data is None:
        user_data = {
            'meow_points': 0,
            'meow_timeout': 0,
            'meow_count': 0,
            'meow_level': 1,
            'meow_xp': 0,
            'total_meows': 0,
            'chat_id': chat_id if chat_type == "Private" else None,
            'group_id': None
        }
        db.set_key(sender_id, user_data)
