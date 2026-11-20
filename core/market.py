# core/market.py
"""موتور بازار میویی - نوسان قیمت محصولات کارخونه بر اساس بازار تصادفی و ثروت کل اقتصاد"""

import time
import random

from core.db_instance import db
from config import (
    FACTORY_PRODUCTS,
    MARKET_UPDATE_INTERVAL_SECONDS,
    MARKET_MULT_MIN,
    MARKET_MULT_MAX,
    MARKET_MULT_REVERSION,
    MARKET_MULT_NOISE,
    ECONOMY_MULT_MIN,
    ECONOMY_MULT_MAX,
    ECONOMY_REFERENCE_AVG_WEALTH,
)

MARKET_STATE_KEY = "market_state"
MAX_HOUR_STEPS_APPLIED = 240  # سقف ایمنی (10 روز) برای جلوگیری از حلقه سنگین بعد از توقف طولانی ربات


def _default_market_state():
    now = time.time()
    return {
        'last_update': now,
        'product_mult': {pid: 1.0 for pid in FACTORY_PRODUCTS},
        'economy_mult': 1.0,
    }


def _calc_economy_mult():
    """ضریب اقتصاد بر اساس میانگین ثروت (پوینت نقدی + موجودی بانک) کل بازیکن‌ ها"""
    all_keys = db.get_all_keys()
    total_wealth = 0
    player_count = 0

    for key in all_keys:
        if not key or not (key.startswith('u') or key.startswith('b')):
            continue
        data = db.get_key(key, None)
        if not isinstance(data, dict) or 'meow_points' not in data:
            continue

        player_count += 1
        total_wealth += data.get('meow_points', 0)
        bank = data.get('bank')
        if isinstance(bank, dict):
            total_wealth += bank.get('balance', 0)

    if player_count == 0:
        return 1.0

    avg_wealth = total_wealth / player_count
    ratio = avg_wealth / ECONOMY_REFERENCE_AVG_WEALTH
    return max(ECONOMY_MULT_MIN, min(ECONOMY_MULT_MAX, ratio))


def _step_product_mult(current):
    """یک قدم نوسان تصادفیِ میانگین‌گرا برای ضریب یک محصول"""
    reverted = current + (1.0 - current) * MARKET_MULT_REVERSION
    noise = random.uniform(-MARKET_MULT_NOISE, MARKET_MULT_NOISE)
    new_value = reverted + noise
    return max(MARKET_MULT_MIN, min(MARKET_MULT_MAX, new_value))


def get_market_state():
    """
    وضعیت فعلی بازار را برمی‌گرداند و در صورت لزوم (گذشت حداقل 1 ساعت) آن را
    به‌صورت تنبل (lazy) به‌روزرسانی می‌کند.
    """
    state = db.get_key(MARKET_STATE_KEY, None)
    if not isinstance(state, dict):
        state = _default_market_state()
        db.set_key(MARKET_STATE_KEY, state)
        return state

    # اطمینان از وجود همه محصولات فعلی (اگر محصول جدیدی به بازی اضافه شده باشد)
    for pid in FACTORY_PRODUCTS:
        state.setdefault('product_mult', {}).setdefault(pid, 1.0)

    now = time.time()
    elapsed = now - state.get('last_update', now)
    hour_steps = int(elapsed // MARKET_UPDATE_INTERVAL_SECONDS)

    if hour_steps <= 0:
        return state

    hour_steps = min(hour_steps, MAX_HOUR_STEPS_APPLIED)

    for _ in range(hour_steps):
        for pid in state['product_mult']:
            state['product_mult'][pid] = _step_product_mult(state['product_mult'][pid])

    # ضریب اقتصاد فقط یک‌بار در هر سینک محاسبه میشه (نه به ازای هر ساعت) چون هزینه محاسباتی داره
    state['economy_mult'] = _calc_economy_mult()
    state['last_update'] = state.get('last_update', now) + hour_steps * MARKET_UPDATE_INTERVAL_SECONDS

    db.set_key(MARKET_STATE_KEY, state)
    return state


def get_product_price(product_id):
    """قیمت لحظه‌ای یک محصول (بعد از اعمال نوسان بازار و ضریب اقتصاد)"""
    if product_id not in FACTORY_PRODUCTS:
        return 0

    state = get_market_state()
    base_price = FACTORY_PRODUCTS[product_id]['base_price']
    market_mult = state['product_mult'].get(product_id, 1.0)
    economy_mult = state.get('economy_mult', 1.0)

    return max(1, int(base_price * market_mult * economy_mult))


def get_all_prices():
    """دیکشنری قیمت فعلی همه محصولات (برای نمایش وضعیت بازار)"""
    state = get_market_state()
    prices = {}
    for pid, info in FACTORY_PRODUCTS.items():
        market_mult = state['product_mult'].get(pid, 1.0)
        economy_mult = state.get('economy_mult', 1.0)
        prices[pid] = max(1, int(info['base_price'] * market_mult * economy_mult))
    return prices


def get_price_trend_label(product_id):
    """برچسب ساده صعودی/نزولی/خنثی برای نمایش کنار قیمت"""
    state = get_market_state()
    mult = state['product_mult'].get(product_id, 1.0)
    if mult >= 1.15:
        return "📈 گرون"
    if mult <= 0.85:
        return "📉 ارزون"
    return "➖ عادی"
