# core/antilink.py
"""ماژول جلوگیری از ارسال لینک در گروه‌ها"""

import re

from config import ADMIN_ID

# الگوی تشخیص لینک (HTTP, HTTPS, WWW)
URL_PATTERN = re.compile(
    r'(https?://\S+)|(www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
    re.IGNORECASE
)

def has_link(text: str) -> bool:
    """بررسی وجود لینک در متن"""
    return bool(URL_PATTERN.search(text))

def handle_antilink(sender_id,text: str, chat_type: str, chat_id: str, message_id: str, bot) -> bool:
    """
    هندلر آنتی‌لینک – در صورت تشخیص لینک، پیام هشدار ارسال می‌کند.
    
    Args:
        text: متن پیام
        chat_type: نوع چت (Group, Private, ...)
        chat_id: شناسه چت
        message_id: شناسه پیام
        bot: نمونه از API

    Returns:
        bool: True اگر لینک یافت شده و پیام مسدود شد، در غیر این صورت False
    """

    if sender_id in ADMIN_ID:
            return False
    
    if chat_type not in ("Group", "SuperGroup"):
        return False

    if has_link(text):
        bot.deleteMessage(chat_id, message_id)
        return True

    return False