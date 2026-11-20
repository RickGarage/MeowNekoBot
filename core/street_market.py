# core/street_market.py
"""منطق مارکت میویی - خرید پیشی خیابونی و کرم ماهیگیری، با سقف خرید روزانه"""

import time

from config import (
    MARKET_CITY_LEVEL_REQUIRED,
    MARKET_DAILY_LIMIT,
    MARKET_STREET_CAT_PRICE,
    MARKET_WORM_PRICE,
)


def get_today_index():
    return int(time.time() // 86400)


def get_daily_purchased(user_data):
    market = user_data.get('market_daily')
    if not isinstance(market, dict) or market.get('day') != get_today_index():
        return 0
    return market.get('purchased', 0)


def get_remaining_daily(user_data):
    return max(0, MARKET_DAILY_LIMIT - get_daily_purchased(user_data))


def register_purchase(user_data, qty):
    today = get_today_index()
    market = user_data.get('market_daily')
    if not isinstance(market, dict) or market.get('day') != today:
        market = {'day': today, 'purchased': 0}
    market['purchased'] += qty
    user_data['market_daily'] = market
    return market['purchased']
