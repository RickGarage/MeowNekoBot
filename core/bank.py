# core/bank.py
"""منطق بانک میویی - افتتاح حساب، سود روزانه، واریز/برداشت، کارت‌به‌کارت"""

import time
import random

from core.db_instance import db
from config import (
    BANK_MIN_LEVEL,
    BANK_OPEN_COST,
    BANK_CHANGE_NUMBER_COST,
    BANK_CHANGE_NUMBER_COOLDOWN,
    BANK_DAILY_INTEREST_RATE,
    BANK_MAX_DAILY_INTEREST,
    BANK_TRANSFER_FEE_RATE,
    BANK_TRANSFER_FEE_MIN,
    BANK_TRANSFER_FEE_MAX,
)

DAY_SECONDS = 24 * 3600
MAX_INTEREST_DAYS_APPLIED = 3650  # سقف ایمنی برای جلوگیری از حلقه بی‌نهایت


def _acct_key(account_number):
    return f"bank_acct:{account_number}"


def has_account(user_data):
    return isinstance(user_data.get('bank'), dict)


def generate_account_number():
    while True:
        number = ''.join(str(random.randint(0, 9)) for _ in range(12))
        if db.get_key(_acct_key(number), None) is None:
            return number


def get_owner_by_account_number(account_number):
    return db.get_key(_acct_key(account_number), None)


def open_account(sender_id, user_data):
    """حساب بانکی جدید باز می‌کند (فرض بر اینه شرایط قبلاً چک شده)"""
    number = generate_account_number()
    user_data['bank'] = {
        'account_number': number,
        'balance': 0,
        'last_interest_at': time.time(),
        'last_number_change': 0,
    }
    db.set_key(_acct_key(number), sender_id)
    return user_data['bank']


def change_account_number(sender_id, user_data):
    bank = user_data['bank']
    old_number = bank['account_number']

    new_number = generate_account_number()
    bank['account_number'] = new_number
    bank['last_number_change'] = time.time()

    db.remove(_acct_key(old_number))
    db.set_key(_acct_key(new_number), sender_id)

    return new_number


def sync_interest(user_data):
    """
    سود روزانه معوقه را محاسبه و به موجودی اضافه می‌کند (بر اساس تعداد روزهای کامل سپری‌شده).

    Returns:
        int: مجموع سودی که در این سینک اضافه شد
    """
    bank = user_data.get('bank')
    if not bank:
        return 0

    now = time.time()
    last = bank.get('last_interest_at', now)
    elapsed = now - last

    days_passed = int(elapsed // DAY_SECONDS)
    if days_passed <= 0:
        return 0

    days_passed = min(days_passed, MAX_INTEREST_DAYS_APPLIED)

    total_interest = 0
    balance = bank.get('balance', 0)

    for _ in range(days_passed):
        day_interest = min(int(balance * BANK_DAILY_INTEREST_RATE), BANK_MAX_DAILY_INTEREST)
        balance += day_interest
        total_interest += day_interest

    bank['balance'] = balance
    bank['last_interest_at'] = last + days_passed * DAY_SECONDS

    return total_interest


def can_change_number(user_data):
    bank = user_data['bank']
    last_change = bank.get('last_number_change', 0)
    remaining = BANK_CHANGE_NUMBER_COOLDOWN - (time.time() - last_change)
    return remaining <= 0, max(0, int(remaining))


def deposit(user_data, amount):
    """انتقال از میو پوینت به موجودی بانک"""
    user_data['meow_points'] = user_data.get('meow_points', 0) - amount
    user_data['bank']['balance'] = user_data['bank'].get('balance', 0) + amount
    return user_data


def withdraw(user_data, amount):
    """انتقال از موجودی بانک به میو پوینت"""
    user_data['bank']['balance'] = user_data['bank'].get('balance', 0) - amount
    user_data['meow_points'] = user_data.get('meow_points', 0) + amount
    return user_data


def calc_transfer_fee(amount):
    fee = int(amount * BANK_TRANSFER_FEE_RATE)
    fee = max(BANK_TRANSFER_FEE_MIN, fee)
    fee = min(BANK_TRANSFER_FEE_MAX, fee)
    return fee
