# core/street_cats.py
"""منطق رویداد پیشی‌های خیابونی - ظاهر شدن تصادفی، تلاش‌های نجات گروهی، جایزه و انقضا"""

import time
import random

from core.db_instance import db
from core.groups import get_group_data, register_group, get_city_level

MAX_ATTEMPTS = 3
EVENT_DURATION_SECONDS = 300        # 5 دقیقه
ATTEMPT_BASE_COST = 500             # هزینه تلاش اول
SUCCESS_CHANCE = 0.30                # شانس موفقیت هر تلاش
REWARD_RANGE = (1000, 5000)          # پاداش نجات موفق

SPAWN_CHANCE_PER_CITY_LEVEL = 0.02   # شانس ظاهر شدن به ازای هر سطح شهر (روی هر میو)
MAX_SPAWN_CHANCE = 0.20


def attempt_cost(attempts_used):
    """هزینه تلاش بعدی (بعد از هر شکست گرون‌تر میشه)"""
    return int(ATTEMPT_BASE_COST * (2 ** attempts_used))


def _is_expired(event):
    return time.time() >= event.get('expires_at', 0)


def get_active_event(chat_id):
    """
    رویداد فعال پیشی خیابونی در این گروه را برمی‌گرداند (در صورت وجود و عدم انقضا).
    اگر منقضی شده باشد، به‌صورت خودکار پاک می‌شود و None برگردانده می‌شود.
    """
    group_data = get_group_data(chat_id)
    if not group_data:
        return None

    event = group_data.get('street_cat_event')
    if not event or not event.get('active'):
        return None

    if _is_expired(event):
        clear_event(chat_id)
        return None

    return event


def clear_event(chat_id):
    group_data = get_group_data(chat_id)
    if group_data and 'street_cat_event' in group_data:
        group_data['street_cat_event'] = None
        db.set_key(chat_id, group_data)


def check_and_expire(chat_id):
    """
    بررسی می‌کند آیا رویداد فعال منقضی شده. اگر بله، پاکش می‌کند و True برمی‌گرداند
    (برای اطلاع‌رسانی به گروه که پیشی از دست رفت).
    """
    group_data = get_group_data(chat_id)
    if not group_data:
        return False

    event = group_data.get('street_cat_event')
    if not event or not event.get('active'):
        return False

    if _is_expired(event):
        clear_event(chat_id)
        return True

    return False


def maybe_spawn_event(chat_id, bot=None):
    """
    با احتمالی متناسب با سطح شهر، ممکنه یه رویداد جدید پیشی خیابونی رو در این گروه شروع کنه
    (فقط اگر رویداد فعالی از قبل وجود نداشته باشد).

    Returns:
        dict یا None: رویداد جدید در صورت ظاهر شدن
    """
    group_data = register_group(chat_id, bot)
    if group_data is None:
        return None

    existing = group_data.get('street_cat_event')
    if existing and existing.get('active') and not _is_expired(existing):
        return None

    city_level = get_city_level(chat_id)
    spawn_chance = min(MAX_SPAWN_CHANCE, SPAWN_CHANCE_PER_CITY_LEVEL * city_level)

    if random.random() >= spawn_chance:
        return None

    now = time.time()
    event = {
        'active': True,
        'attempts_used': 0,
        'max_attempts': MAX_ATTEMPTS,
        'created_at': now,
        'expires_at': now + EVENT_DURATION_SECONDS,
    }
    group_data['street_cat_event'] = event
    db.set_key(chat_id, group_data)
    return event


def attempt_rescue(chat_id, sender_id):
    """
    یک تلاش برای نجات پیشی خیابونی فعال در این گروه.

    Returns:
        dict با کلید 'result' یکی از:
        'no_event', 'not_enough_points', 'success', 'fail', 'lost'
        و سایر جزئیات (cost, reward, attempts_left, attempts_used)
    """
    event = get_active_event(chat_id)
    if not event:
        return {'result': 'no_event'}

    cost = attempt_cost(event['attempts_used'])

    user_data = db.get_key(sender_id, {})
    if not isinstance(user_data, dict):
        user_data = {}

    user_points = user_data.get('meow_points', 0)
    if user_points < cost:
        return {'result': 'not_enough_points', 'cost': cost}

    # هزینه تلاش صرف نظر از نتیجه کسر میشه
    user_data['meow_points'] = user_points - cost
    db.set_key(sender_id, user_data)

    success = random.random() < SUCCESS_CHANCE

    group_data = get_group_data(chat_id)

    if success:
        reward = random.randint(*REWARD_RANGE)
        user_data = db.get_key(sender_id, {})
        user_data['meow_points'] = user_data.get('meow_points', 0) + reward
        user_data['rescued_cats_count'] = user_data.get('rescued_cats_count', 0) + 1
        db.set_key(sender_id, user_data)

        if group_data:
            group_data['street_cat_event'] = None
            group_data['total_rescued'] = group_data.get('total_rescued', 0) + 1
            db.set_key(chat_id, group_data)

        return {
            'result': 'success',
            'cost': cost,
            'reward': reward,
            'total_rescued': user_data['rescued_cats_count'],
        }

    # شکست این تلاش
    event['attempts_used'] += 1

    if event['attempts_used'] >= event['max_attempts']:
        if group_data:
            group_data['street_cat_event'] = None
            db.set_key(chat_id, group_data)
        return {'result': 'lost', 'cost': cost}

    if group_data:
        group_data['street_cat_event'] = event
        db.set_key(chat_id, group_data)

    next_cost = attempt_cost(event['attempts_used'])
    attempts_left = event['max_attempts'] - event['attempts_used']

    return {
        'result': 'fail',
        'cost': cost,
        'attempts_left': attempts_left,
        'next_cost': next_cost,
    }
