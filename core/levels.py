"""منطق سیستم سطح‌بندی کاربران"""

from config import LEVEL_CONFIG, MAX_LEVEL
from core.db_instance import db


def get_level_config(level):
    """دریافت تنظیمات سطح با الگوی افزایشی"""
    if level <= MAX_LEVEL:
        return LEVEL_CONFIG.get(level, LEVEL_CONFIG[MAX_LEVEL])

    base_level = MAX_LEVEL
    diff = level - base_level

    meows_needed = LEVEL_CONFIG[MAX_LEVEL]['meows_needed'] + (diff * 250)
    points_min = LEVEL_CONFIG[MAX_LEVEL]['points_range'][0] + (diff * 30)
    points_max = LEVEL_CONFIG[MAX_LEVEL]['points_range'][1] + (diff * 40)
    cooldown = max(180, LEVEL_CONFIG[MAX_LEVEL]['cooldown'] - (diff * 5))
    bonus = LEVEL_CONFIG[MAX_LEVEL]['bonus'] + (diff * 15000)

    return {
        'meows_needed': meows_needed,
        'points_range': (points_min, points_max),
        'cooldown': cooldown,
        'bonus': bonus
    }


def get_user_level_data(user_id):
    user_data = db.get_key(user_id, {
        'meow_points': 0,
        'meow_timeout': 0,
        'meow_count': 0,
        'meow_level': 1,
        'meow_xp': 0,
        'total_meows': 0,
        'chat_id': None
    })
    return user_data


def update_user_level(user_id, user_data):
    """
    بروزرسانی سطح کاربر بر اساس XP مستقل از تعداد کل میوها
    با هر میو، یک واحد به XP اضافه می‌شود و وقتی به حد نیاز رسید، سطح ارتقا می‌یابد.
    """
    level = user_data.get('meow_level', 1)
    xp = user_data.get('meow_xp', 0)  # XP مستقل از meow_count
    level_up = False

    # هر بار که تابع صدا زده می‌شود (یعنی یک میو موفق)، یک واحد به XP اضافه می‌کنیم
    xp += 1
    user_data['meow_xp'] = xp

    current_config = get_level_config(level)
    next_config = get_level_config(level + 1)

    if level < MAX_LEVEL + 10:
        xp_needed = next_config['meows_needed'] - current_config['meows_needed']

        # تا زمانی که XP به اندازه کافی است، سطح را ارتقا بده
        while xp >= xp_needed and level < MAX_LEVEL + 10:
            # دریافت پاداش ارتقا
            bonus = next_config['bonus']
            user_data['meow_points'] = user_data.get('meow_points', 0) + bonus

            # افزایش سطح
            level = level + 1
            user_data['meow_level'] = level
            level_up = True

            # کاهش XP به اندازه نیاز سطح قبلی
            xp = xp - xp_needed
            user_data['meow_xp'] = xp

            # به‌روزرسانی config برای سطح جدید
            current_config = get_level_config(level)
            next_config = get_level_config(level + 1)
            if level < MAX_LEVEL + 10:
                xp_needed = next_config['meows_needed'] - current_config['meows_needed']
            else:
                break
    else:
        user_data['meow_xp'] = 0

    if level_up:
        user_data['level_up'] = True

    return user_data


def get_level_bar(user_id, level, xp):
    """دریافت نوار پیشرفت سطح"""
    if level >= MAX_LEVEL + 10:
        return f"⭐️ سطح {level} | MAX"

    current_config = get_level_config(level)
    next_config = get_level_config(level + 1)

    xp_needed = next_config['meows_needed'] - current_config['meows_needed']
    xp_current = min(xp, xp_needed)

    progress = int((xp_current / xp_needed) * 10) if xp_needed > 0 else 0
    bar = "▰" * progress + "▱" * (10 - progress)

    return f"⭐️ سطح {level} | {xp_current}/{xp_needed} {bar}"


def get_cooldown_for_level(level):
    config = get_level_config(level)
    return config['cooldown']


def get_points_range_for_level(level):
    config = get_level_config(level)
    return config['points_range']


def get_xp_info(level):
    """دریافت اطلاعات XP مورد نیاز برای سطح فعلی و بعدی"""
    current_config = get_level_config(level)
    next_config = get_level_config(level + 1)
    xp_needed = next_config['meows_needed'] - current_config['meows_needed']
    return {
        'xp_needed': xp_needed,
        'current_meows_needed': current_config['meows_needed'],
        'next_meows_needed': next_config['meows_needed']
    }