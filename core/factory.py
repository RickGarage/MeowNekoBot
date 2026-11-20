# core/factory.py
"""منطق کارخونه میویی - انبار، کارگران (پیشی‌های خیابونی نجات‌داده)، دستگاه تولید، سطح‌بندی"""

import time

from config import (
    FACTORY_MIN_LEVEL,
    FACTORY_BUILD_COST,
    WAREHOUSE_BASE_CAPACITY,
    WAREHOUSE_CAPACITY_PER_LEVEL,
    WAREHOUSE_UPGRADE_COST_BASE,
    MACHINE_BASE_CYCLE_SECONDS,
    MACHINE_CYCLE_REDUCTION_PER_LEVEL,
    MACHINE_MIN_CYCLE_SECONDS,
    MACHINE_UPGRADE_COST_BASE,
    FACTORY_LEVEL_EXP_BASE,
    FACTORY_PRODUCTS,
)

MAX_PRODUCTION_CYCLES_APPLIED = 100000  # سقف ایمنی برای جلوگیری از حلقه سنگین


def has_factory(user_data):
    return isinstance(user_data.get('factory'), dict)


def create_factory():
    return {
        'level': 1,
        'exp': 0,
        'warehouse_level': 1,
        'machine_level': 1,
        'workers': 0,
        'stored_products': {},
        'current_product': None,
        'last_production_at': time.time(),
    }


def warehouse_capacity(factory):
    return WAREHOUSE_BASE_CAPACITY + WAREHOUSE_CAPACITY_PER_LEVEL * (factory.get('warehouse_level', 1) - 1)


def warehouse_upgrade_cost(factory):
    return int(WAREHOUSE_UPGRADE_COST_BASE * factory.get('warehouse_level', 1))


def cycle_seconds(factory):
    reduction = MACHINE_CYCLE_REDUCTION_PER_LEVEL * (factory.get('machine_level', 1) - 1)
    return max(MACHINE_MIN_CYCLE_SECONDS, MACHINE_BASE_CYCLE_SECONDS - reduction)


def machine_upgrade_cost(factory):
    return int(MACHINE_UPGRADE_COST_BASE * factory.get('machine_level', 1))


def total_stored(factory):
    return sum(factory.get('stored_products', {}).values())


def level_up_threshold(level):
    return FACTORY_LEVEL_EXP_BASE * level


def get_unlocked_products(factory_level):
    return [pid for pid, info in FACTORY_PRODUCTS.items() if info['unlock_level'] <= factory_level]


def available_workers_to_hire(user_data):
    factory = user_data.get('factory') or {}
    rescued = user_data.get('rescued_cats_count', 0)
    hired = factory.get('workers', 0)

    smuggling = user_data.get('smuggling') or {}
    in_transit = smuggling.get('cat_count', 0) if smuggling.get('active') else 0

    return max(0, rescued - hired - in_transit)


def hire_workers(user_data, amount):
    factory = user_data['factory']
    available = available_workers_to_hire(user_data)
    amount = min(amount, available)
    factory['workers'] = factory.get('workers', 0) + amount
    return amount


def fire_workers(factory, amount):
    current = factory.get('workers', 0)
    amount = min(amount, current)
    factory['workers'] = current - amount
    return amount


def _try_level_up(factory):
    leveled_up_to = None
    while factory['exp'] >= level_up_threshold(factory['level']):
        factory['exp'] -= level_up_threshold(factory['level'])
        factory['level'] += 1
        leveled_up_to = factory['level']
    return leveled_up_to


def sync_production(factory):
    """
    بر اساس زمان سپری‌شده، کارگران و سرعت دستگاه، محصولات جدید تولید و به انبار اضافه می‌کند.
    ظرفیت انبار و سطح کارخونه (از طریق exp) نیز به‌روزرسانی می‌شود.

    Returns:
        dict: {'produced': int, 'product_id': str|None, 'leveled_up_to': int|None}
    """
    now = time.time()
    last = factory.get('last_production_at', now)
    workers = factory.get('workers', 0)
    product_id = factory.get('current_product')

    result = {'produced': 0, 'product_id': product_id, 'leveled_up_to': None}

    if not product_id or workers <= 0 or product_id not in FACTORY_PRODUCTS:
        factory['last_production_at'] = now
        return result

    cycle = cycle_seconds(factory)
    elapsed = now - last
    cycles_passed = int(elapsed // cycle)

    if cycles_passed <= 0:
        return result

    cycles_passed = min(cycles_passed, MAX_PRODUCTION_CYCLES_APPLIED)

    capacity = warehouse_capacity(factory)
    current_stored = total_stored(factory)
    space_left = max(0, capacity - current_stored)

    potential_produced = cycles_passed * workers
    actually_produced = min(potential_produced, space_left)

    if actually_produced > 0:
        stored = factory.setdefault('stored_products', {})
        stored[product_id] = stored.get(product_id, 0) + actually_produced

        exp_gain = actually_produced * FACTORY_PRODUCTS[product_id]['exp']
        factory['exp'] = factory.get('exp', 0) + exp_gain

        result['produced'] = actually_produced
        result['leveled_up_to'] = _try_level_up(factory)

    # زمان رو فقط به اندازه سیکل‌های واقعا مصرف‌شده جلو می‌بریم (باقیمانده برای دفعه بعد می‌مونه)
    factory['last_production_at'] = last + cycles_passed * cycle

    return result
