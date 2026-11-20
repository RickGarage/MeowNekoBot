# core/ranking.py
"""توابع مربوط به رتبه‌بندی و لیدربرد کاربران"""

from core.db_instance import db


def get_top_users(by='points', limit=5):
    """دریافت کاربران برتر"""
    all_users = db.get_all_keys()
    user_list = []

    for uid in all_users:
        if not uid:
            continue
        # فقط کاربران واقعی (شروع با u یا b)
        if uid.startswith('u') or uid.startswith('b'):
            data = db.get_key(uid, {})
            # بررسی اینکه data دیکشنری باشد
            if isinstance(data, dict) and data:
                if by == 'points':
                    value = data.get('meow_points', 0)
                else:
                    value = data.get('meow_count', 0)
                # فقط کاربرانی که مقدارشان بیشتر از 0 است
                if value > 0:
                    user_list.append((uid, value, data))

    # مرتب‌سازی نزولی
    user_list.sort(key=lambda x: x[1], reverse=True)
    return user_list[:limit]


def get_rotbe_meow_points(user_id):
    """دریافت رتبه کاربر بر اساس میو پوینت"""
    all_users = db.get_all_keys()
    points_list = []

    for uid in all_users:
        if not uid:
            continue
        if uid.startswith('u') or uid.startswith('b'):  # فقط کاربران
            data = db.get_key(uid, {})
            if isinstance(data, dict) and data:
                points = data.get('meow_points', 0)
                if points > 0:  # فقط کاربرانی که پوینت دارند
                    points_list.append((uid, points))

    # مرتب‌سازی بر اساس پوینت (نزولی)
    points_list.sort(key=lambda x: x[1], reverse=True)

    # پیدا کردن رتبه کاربر
    for idx, (uid, _) in enumerate(points_list, 1):
        if uid == user_id:
            return f"{idx:,}"

    return "نامشخص"


def get_rotbe_meow_count(user_id):
    """دریافت رتبه کاربر بر اساس تعداد میو"""
    all_users = db.get_all_keys()
    count_list = []

    for uid in all_users:
        if not uid:
            continue
        if uid.startswith('u') or uid.startswith('b'):  # فقط کاربران
            data = db.get_key(uid, {})
            if isinstance(data, dict) and data:
                count = data.get('meow_count', 0)
                if count > 0:  # فقط کاربرانی که میو دارند
                    count_list.append((uid, count))

    # مرتب‌سازی بر اساس تعداد میو (نزولی)
    count_list.sort(key=lambda x: x[1], reverse=True)

    # پیدا کردن رتبه کاربر
    for idx, (uid, _) in enumerate(count_list, 1):
        if uid == user_id:
            return f"{idx:,}"

    return "نامشخص"
