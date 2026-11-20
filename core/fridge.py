# core/fridge.py
"""منطق یخچال میویی - ذخیره یک واحد از هر نوع ماهی و پخت‌وپز برای افزایش ارزش"""

import time

from config import (
    FRIDGE_UNLOCK_LEVEL,
    FRIDGE_BASE_CAPACITY,
    FRIDGE_UPGRADE_COST_BASE,
    COOK_SECONDS_PER_001KG,
    COOK_SELL_MULTIPLIER,
    COOK_FEED_MULTIPLIER,
)



def has_fridge_access(user_data):
    return user_data.get('meow_level', 1) >= FRIDGE_UNLOCK_LEVEL


def get_fridge(user_data):
    fridge = user_data.get('fridge')
    if not isinstance(fridge, list):
        fridge = []
    return fridge


def get_fridge_capacity(user_data):
    return user_data.get('fridge_capacity', FRIDGE_BASE_CAPACITY)


def fridge_upgrade_cost(current_capacity):
    return int(FRIDGE_UPGRADE_COST_BASE * current_capacity)


def find_slot_index(fridge, name):
    for idx, entry in enumerate(fridge):
        if entry['name'] == name:
            return idx
    return None


def cook_time_seconds(weight_kg):
    return max(1, int(round((weight_kg / 0.01) * COOK_SECONDS_PER_001KG)))


def sync_cooking(entry):
    """اگر زمان پخت این ماهی تموم شده باشه، وضعیتش رو به 'پخته‌شده' تغییر میده"""
    if entry.get('cooking') and not entry.get('cooked'):
        ready_at = entry.get('cook_ready_at', 0)
        if time.time() >= ready_at:
            entry['cooking'] = False
            entry['cooked'] = True
    return entry


def sync_all_fridge(fridge):
    for entry in fridge:
        sync_cooking(entry)
    return fridge


def effective_sell_price(entry):
    base = entry['unit_price']
    return base * COOK_SELL_MULTIPLIER if entry.get('cooked') else base


def effective_feed_multiplier(entry):
    return COOK_FEED_MULTIPLIER if entry.get('cooked') else 1


def create_fridge_entry(name, unit_price, weight):
    return {
        'name': name,
        'unit_price': unit_price,
        'weight': weight,
        'frozen_at': time.time(),
        'cooking': False,
        'cook_ready_at': None,
        'cooked': False,
    }
