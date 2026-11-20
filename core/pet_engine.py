# core/pet_engine.py
"""موتور منطقی سیستم پیشی (Pet) - تولید پوینت، ظرفیت، تغذیه، سطح و مقام"""

import time

from config import (
    PET_PRICE,
    PET_MIN_USER_LEVEL,
    PET_BASE_RATE_PER_SEC,
    PET_BASE_CAPACITY,
    PET_LEVELS_PER_RANK,
    PET_UPGRADE_BASE_COST,
    PET_RANKUP_BASE_COST,
    PET_FEED_ENERGY_SECONDS,
    PET_BASE_MAX_ENERGY_MEALS,
    PET_EXTRA_MEALS_PER_RANK,
)
from core.db_instance import db


def has_pet(user_data):
    return isinstance(user_data.get('pet'), dict)


def create_pet():
    now = time.time()
    return {
        'name': None,
        'level': 1,
        'rank': 1,
        'box_points': 0.0,
        'last_collect': now,
        'energy_until': now,  # صفر یعنی شکمش خالیه (تازه خریداری شده)
        'created_at': now,
    }


def get_rate_per_sec(pet):
    """سرعت تولید پوینت در ثانیه بر اساس سطح فعلی"""
    return PET_BASE_RATE_PER_SEC * pet.get('level', 1)


def get_capacity(pet):
    """ظرفیت جعبه بر اساس سطح و مقام"""
    return PET_BASE_CAPACITY * pet.get('level', 1) * pet.get('rank', 1)


def get_level_cap(pet):
    """سقف سطح مجاز برای مقام فعلی"""
    return PET_LEVELS_PER_RANK * pet.get('rank', 1)


def get_upgrade_cost(pet):
    """هزینه ارتقا یک سطح"""
    return PET_UPGRADE_BASE_COST * pet.get('level', 1)


def get_rankup_cost(pet):
    """هزینه ارتقا مقام"""
    return PET_RANKUP_BASE_COST * pet.get('rank', 1)


def get_max_banked_energy(pet):
    """حداکثر انرژی (بر حسب ثانیه) که پیشی میتونه از قبل ذخیره کنه - وابسته به مقام"""
    rank = pet.get('rank', 1)
    max_meals = PET_BASE_MAX_ENERGY_MEALS + (rank - 1) * PET_EXTRA_MEALS_PER_RANK
    return max_meals * PET_FEED_ENERGY_SECONDS


def is_fed(pet, now=None):
    now = now or time.time()
    return pet.get('energy_until', 0) > now


def update_pet_production(pet):
    """
    محاسبه پوینت‌های تولید شده از آخرین بار تا الان و اضافه کردن به جعبه.
    این تابع باید قبل از هر عملیاتی روی پیشی (نمایش وضعیت، برداشت، ارتقا و ...) صدا زده بشه.
    """
    now = time.time()
    last_collect = pet.get('last_collect', now)
    energy_until = pet.get('energy_until', 0)

    # بازه‌ای که پیشی واقعا سیر و فعال بوده (تا الان یا تا وقتی گشنش شده، هر کدوم زودتره)
    productive_until = min(now, energy_until)

    if productive_until > last_collect:
        elapsed = productive_until - last_collect
        rate = get_rate_per_sec(pet)
        capacity = get_capacity(pet)

        produced = elapsed * rate
        pet['box_points'] = min(capacity, pet.get('box_points', 0.0) + produced)

    pet['last_collect'] = now
    return pet


def buy_pet(sender_id, user_data):
    """
    تلاش برای خرید پیشی.
    Returns: (success: bool, reason: str)
    reason یکی از: 'ok', 'already_has_pet', 'level_too_low', 'not_enough_points'
    """
    if has_pet(user_data):
        return False, 'already_has_pet'

    if user_data.get('meow_level', 1) < PET_MIN_USER_LEVEL:
        return False, 'level_too_low'

    if user_data.get('meow_points', 0) < PET_PRICE:
        return False, 'not_enough_points'

    user_data['meow_points'] -= PET_PRICE
    user_data['pet'] = create_pet()
    db.set_key(sender_id, user_data)
    return True, 'ok'


def collect_pet_points(sender_id, user_data):
    """برداشت پوینت‌های جمع شده در جعبه پیشی و افزودن به موجودی کاربر"""
    pet = user_data.get('pet')
    if not pet:
        return 0, user_data

    pet = update_pet_production(pet)
    collected = int(pet.get('box_points', 0))

    if collected > 0:
        pet['box_points'] = pet.get('box_points', 0) - collected
        user_data['meow_points'] = user_data.get('meow_points', 0) + collected

    user_data['pet'] = pet
    db.set_key(sender_id, user_data)
    return collected, user_data


def feed_pet(sender_id, user_data):
    """
    تغذیه پیشی با یک ماهی از انبار (ارزون‌ترین ماهی موجود مصرف میشه تا ماهی‌های
    ارزشمند برای فروش باقی بمونن).

    Returns: (success: bool, reason: str, fish_name: str|None)
    reason یکی از: 'ok', 'no_pet', 'no_fish', 'energy_full'
    """
    pet = user_data.get('pet')
    if not pet:
        return False, 'no_pet', None

    pet = update_pet_production(pet)

    inventory = user_data.get('fish_inventory', [])
    if not isinstance(inventory, list) or not inventory:
        user_data['pet'] = pet
        return False, 'no_fish', None

    now = time.time()
    max_energy = get_max_banked_energy(pet)
    current_banked = max(0, pet.get('energy_until', 0) - now)

    if current_banked >= max_energy:
        user_data['pet'] = pet
        return False, 'energy_full', None

    # پیدا کردن ارزون‌ترین دسته ماهی موجود
    cheapest_idx = None
    for idx, stack in enumerate(inventory):
        if stack.get('count', 0) <= 0:
            continue
        if cheapest_idx is None or stack['unit_price'] < inventory[cheapest_idx]['unit_price']:
            cheapest_idx = idx

    if cheapest_idx is None:
        user_data['pet'] = pet
        return False, 'no_fish', None

    fish_name = inventory[cheapest_idx]['name']
    inventory[cheapest_idx]['count'] -= 1
    if inventory[cheapest_idx]['count'] <= 0:
        inventory.pop(cheapest_idx)

    base_point = now if pet.get('energy_until', 0) < now else pet.get('energy_until', 0)
    new_energy_until = min(base_point + PET_FEED_ENERGY_SECONDS, now + max_energy)
    pet['energy_until'] = new_energy_until

    user_data['fish_inventory'] = inventory
    user_data['pet'] = pet
    db.set_key(sender_id, user_data)

    return True, 'ok', fish_name


def upgrade_pet_level(sender_id, user_data):
    """
    ارتقا سطح پیشی با پرداخت پوینت.
    Returns: (success: bool, reason: str, cost: int)
    reason یکی از: 'ok', 'no_pet', 'level_capped', 'not_enough_points'
    """
    pet = user_data.get('pet')
    if not pet:
        return False, 'no_pet', 0

    pet = update_pet_production(pet)

    level_cap = get_level_cap(pet)
    if pet.get('level', 1) >= level_cap:
        user_data['pet'] = pet
        return False, 'level_capped', 0

    cost = get_upgrade_cost(pet)
    if user_data.get('meow_points', 0) < cost:
        user_data['pet'] = pet
        return False, 'not_enough_points', cost

    user_data['meow_points'] -= cost
    pet['level'] = pet.get('level', 1) + 1
    user_data['pet'] = pet
    db.set_key(sender_id, user_data)

    return True, 'ok', cost


def rankup_pet(sender_id, user_data):
    """
    ارتقا مقام پیشی. فقط وقتی سطح پیشی به سقف مقام فعلی رسیده باشه ممکنه.
    سطح و پوینت جعبه صفر میشه، اما سقف سطح و ظرفیت شکم افزایش پیدا میکنه.

    Returns: (success: bool, reason: str, cost: int)
    reason یکی از: 'ok', 'no_pet', 'level_not_maxed', 'not_enough_points'
    """
    pet = user_data.get('pet')
    if not pet:
        return False, 'no_pet', 0

    pet = update_pet_production(pet)

    level_cap = get_level_cap(pet)
    if pet.get('level', 1) < level_cap:
        user_data['pet'] = pet
        return False, 'level_not_maxed', 0

    cost = get_rankup_cost(pet)
    if user_data.get('meow_points', 0) < cost:
        user_data['pet'] = pet
        return False, 'not_enough_points', cost

    user_data['meow_points'] -= cost
    pet['rank'] = pet.get('rank', 1) + 1
    pet['level'] = 1
    pet['box_points'] = 0.0
    user_data['pet'] = pet
    db.set_key(sender_id, user_data)

    return True, 'ok', cost


def rename_pet(sender_id, user_data, new_name):
    pet = user_data.get('pet')
    if not pet:
        return False

    pet['name'] = new_name
    user_data['pet'] = pet
    db.set_key(sender_id, user_data)
    return True
