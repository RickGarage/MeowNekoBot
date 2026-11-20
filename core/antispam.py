# core/antispam.py
"""منطق آنتی‌اسپم و زندان میویی"""

import time
from config import USER_SPAM_LIMIT, SPAM_WINDOW, SPAM_BAN_DURATION,ADMIN_ID
from core.db_instance import db

# دیکشنری برای ذخیره زمان پیام‌های کاربران
user_messages = {}


def check_spam(sender_id) -> bool:
    """
    بررسی اسپم بودن کاربر

    Args:
        sender_id: شناسه کاربر

    Returns:
        bool: True اگر کاربر اسپم نکرده باشد، False اگر اسپم کرده باشد
    """
    
    if sender_id in ADMIN_ID:
        return True
    
    current_time = time.time()

    # دریافت زمان‌های پیام‌های کاربر
    if sender_id not in user_messages:
        user_messages[sender_id] = []

    # پاک کردن پیام‌های قدیمی (بیشتر از بازه زمانی)
    user_messages[sender_id] = [t for t in user_messages[sender_id] if current_time - t < SPAM_WINDOW]

    # اضافه کردن زمان فعلی
    user_messages[sender_id].append(current_time)

    # بررسی تعداد پیام‌ها در بازه زمانی
    if len(user_messages[sender_id]) > USER_SPAM_LIMIT:
        return False

    return True


def get_spam_ban_time(sender_id) -> int:
    """
    دریافت زمان باقی‌مانده از محرومیت کاربر

    Args:
        sender_id: شناسه کاربر

    Returns:
        int: زمان باقی‌مانده بر حسب ثانیه (0 اگر محروم نیست)
    """
    user_data = db.get_key(sender_id, {})
    ban_until = user_data.get('spam_ban_until', 0)
    current_time = time.time()

    if ban_until > current_time:
        return int(ban_until - current_time)
    return 0


def ban_user_for_spam(sender_id):
    """
    قرار دادن کاربر در زندان میویی

    Args:
        sender_id: شناسه کاربر
    """
    user_data = db.get_key(sender_id, {})
    user_data['spam_ban_until'] = time.time() + SPAM_BAN_DURATION
    user_data['spam_count'] = user_data.get('spam_count', 0) + 1
    db.set_key(sender_id, user_data)

    # پاک کردن تاریخچه پیام‌های کاربر
    if sender_id in user_messages:
        user_messages[sender_id] = []


def is_user_banned(sender_id) -> bool:
    """
    بررسی اینکه کاربر در زندان میویی است یا خیر

    Args:
        sender_id: شناسه کاربر

    Returns:
        bool: True اگر کاربر محروم است، False در غیر این صورت
    """
    remaining = get_spam_ban_time(sender_id)
    return remaining > 0


def calculate_fine(remaining_seconds):
    """
    محاسبه جریمه بر اساس زمان باقی‌مانده

    Args:
        remaining_seconds: زمان باقی‌مانده به ثانیه

    Returns:
        int: مبلغ جریمه
    """
    # هر ثانیه = 1 پوینت (حداقل 50 و حداکثر 500)
    fine = remaining_seconds * 1
    fine = max(50, min(fine, 2500))  # محدوده 50 تا 500
    return int(fine)
