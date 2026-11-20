# core/smuggling.py
"""منطق قاچاق میویی - محموله‌ های ریسک/پاداش با پیشی‌ های خیابونی"""

import time
import random

from core.db_instance import db
from core.antispam import user_messages
from config import (
    SMUGGLING_MIN_LEVEL,
    SMUGGLING_MIN_CATS,
    SMUGGLING_MAX_CATS,
    SMUGGLING_SECONDS_PER_CAT,
    SMUGGLING_REWARD_MIN_PER_CAT,
    SMUGGLING_REWARD_MAX_PER_CAT,
    SMUGGLING_BASE_CATCH_CHANCE,
    SMUGGLING_CATCH_CHANCE_PER_CAT,
    SMUGGLING_MAX_CATCH_CHANCE,
    SMUGGLING_JAIL_DURATION,
)


def mission_duration(cat_count):
    return cat_count * SMUGGLING_SECONDS_PER_CAT


def catch_chance(cat_count):
    extra = max(0, cat_count - SMUGGLING_MIN_CATS)
    chance = SMUGGLING_BASE_CATCH_CHANCE + extra * SMUGGLING_CATCH_CHANCE_PER_CAT
    return min(SMUGGLING_MAX_CATCH_CHANCE, chance)


def committed_cats(user_data):
    """تعداد پیشی خیابونی که الان یا استخدام کارخونه شده یا در حال قاچاقه (غیرقابل استفاده مجدد)"""
    factory = user_data.get('factory') or {}
    hired = factory.get('workers', 0)

    smuggling = user_data.get('smuggling') or {}
    in_transit = smuggling.get('cat_count', 0) if smuggling.get('active') else 0

    return hired + in_transit


def available_cats(user_data):
    total = user_data.get('rescued_cats_count', 0)
    return max(0, total - committed_cats(user_data))


def has_active_mission(user_data):
    smuggling = user_data.get('smuggling')
    return bool(smuggling and smuggling.get('active'))


def is_mission_ready(user_data):
    smuggling = user_data.get('smuggling')
    if not smuggling or not smuggling.get('active'):
        return False
    return time.time() >= smuggling.get('ready_at', 0)


def start_mission(user_data, cat_count):
    now = time.time()
    duration = mission_duration(cat_count)
    user_data['smuggling'] = {
        'active': True,
        'cat_count': cat_count,
        'started_at': now,
        'ready_at': now + duration,
    }
    return user_data['smuggling']


def resolve_mission(sender_id, user_data):
    """
    ماموریت آماده‌ی فعلی را حل می‌کند (موفقیت یا لو رفتن) و نتیجه را برمی‌گرداند.

    Returns:
        dict: {'result': 'success'|'caught', 'cat_count':, 'reward':(اگه موفق), 'jail_seconds':(اگه لو رفته)}
    """
    smuggling = user_data['smuggling']
    cat_count = smuggling['cat_count']

    chance = catch_chance(cat_count)
    caught = random.random() < chance

    # پیشی‌ ها در هر دو حالت از دست میرن (فروخته شدن یا مصادره شدن)
    user_data['rescued_cats_count'] = max(0, user_data.get('rescued_cats_count', 0) - cat_count)
    user_data['smuggling'] = None

    if caught:
        user_data['spam_ban_until'] = time.time() + SMUGGLING_JAIL_DURATION
        user_data['spam_count'] = user_data.get('spam_count', 0) + 1
        user_data['smuggling_caught_count'] = user_data.get('smuggling_caught_count', 0) + 1

        if sender_id in user_messages:
            user_messages[sender_id] = []

        return {'result': 'caught', 'cat_count': cat_count, 'jail_seconds': SMUGGLING_JAIL_DURATION}

    reward = sum(random.randint(SMUGGLING_REWARD_MIN_PER_CAT, SMUGGLING_REWARD_MAX_PER_CAT) for _ in range(cat_count))
    user_data['meow_points'] = user_data.get('meow_points', 0) + reward
    user_data['smuggling_success_count'] = user_data.get('smuggling_success_count', 0) + 1
    user_data['smuggling_total_earned'] = user_data.get('smuggling_total_earned', 0) + reward

    return {'result': 'success', 'cat_count': cat_count, 'reward': reward}
