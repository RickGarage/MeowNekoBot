# core/conversations.py
"""مدیریت وضعیت مکالمه های چند مرحله ای (کانورسیشن) کاربران

این ماژول برای فرآیند هایی که نیاز به چند پیام رفت و برگشت دارند استفاده می‌شود
(مثل فروش ماهی، انتقال بانکی، پنل قاچاق و ...). هر کاربر در هر لحظه فقط
می‌تواند در یک کانورسیشن فعال باشد.
"""

import time

from core.db_instance import db

CONVERSATION_TIMEOUT = 300  # 5 دقیقه - بعد از این مدت کانورسیشن خودکار منقضی می‌شود


def _conv_key(sender_id):
    return f"conv:{sender_id}"


def get_conversation(sender_id):
    """دریافت کانورسیشن فعال کاربر (در صورت وجود و عدم انقضا)"""
    conv = db.get_key(_conv_key(sender_id), None)
    if not isinstance(conv, dict):
        return None

    started_at = conv.get('started_at', 0)
    if time.time() - started_at > CONVERSATION_TIMEOUT:
        clear_conversation(sender_id)
        return None

    return conv


def start_conversation(sender_id, name, step, data=None):
    """شروع یک کانورسیشن جدید (یا جایگزینی کانورسیشن قبلی)"""
    conv = {
        'name': name,
        'step': step,
        'data': data or {},
        'started_at': time.time(),
    }
    db.set_key(_conv_key(sender_id), conv)
    return conv


def update_conversation(sender_id, step=None, data=None):
    """به‌روزرسانی مرحله و/یا داده‌های کانورسیشن فعال"""
    conv = get_conversation(sender_id)
    if not conv:
        return None

    if step is not None:
        conv['step'] = step
    if data is not None:
        conv['data'].update(data)

    # هر تعامل جدید، تایمر انقضا را ریست می‌کند
    conv['started_at'] = time.time()

    db.set_key(_conv_key(sender_id), conv)
    return conv


def clear_conversation(sender_id):
    """پایان دادن به کانورسیشن فعال کاربر"""
    db.remove(_conv_key(sender_id))


def is_in_conversation(sender_id, name=None):
    conv = get_conversation(sender_id)
    if not conv:
        return False
    if name is not None:
        return conv.get('name') == name
    return True
