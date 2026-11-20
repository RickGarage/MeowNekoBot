# core/referral.py
"""سیستم کد دعوت میویی"""

import random
import string
import time
from core.db_instance import db
from config import REFERRAL_REWARD_POINTS, REFERRAL_MIN_LEVEL,REFERRAL_REWARD_WALLET


def generate_invite_code(user_id: str) -> str:
    """
    تولید کد دعوت یکتا برای کاربر (در صورت داشتن سطح کافی)
    برگرداندن کد یا None در صورت خطا
    """
    user_data = db.get_key(user_id, {})
    level = user_data.get('meow_level', 1)

    if level < REFERRAL_MIN_LEVEL:
        return None

    # اگر قبلاً کد دارد، همان را برگردان
    if user_data.get('invite_code'):
        return user_data['invite_code']

    # ساخت کد جدید (۶ کاراکتر حروف بزرگ و اعداد)
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(chars, k=6))

    # جلوگیری از تکراری بودن (در صورت نادر بودن)
    while db.get_key(f"invite_code_{code}"):
        code = ''.join(random.choices(chars, k=6))

    # ذخیره کد در دیتابیس
    user_data['invite_code'] = code
    db.set_key(user_id, user_data)
    db.set_key(f"invite_code_{code}", user_id)

    return code


def get_user_by_code(code: str) -> str | None:
    """دریافت شناسه کاربر صاحب کد"""
    return db.get_key(f"invite_code_{code}")


def use_referral_code(new_user_id: str, code: str) -> tuple[bool, str]:
    """
    استفاده از کد دعوت توسط کاربر جدید
    برگرداندن (موفقیت, پیام)
    """
    if not code or len(code) != 6:
        return False, "❌ کد دعوت باید ۶ کاراکتر باشد!"

    referrer_id = get_user_by_code(code)
    if not referrer_id:
        return False, "❌ کد دعوت معتبر نیست!"

    if referrer_id == new_user_id:
        return False, "❌ نمی‌توانی از کد خودت استفاده کنی!"

    # بررسی اینکه کاربر جدید قبلاً کد دعوت استفاده کرده
    new_user_data = db.get_key(new_user_id, {})
    if new_user_data.get('referred_by'):
        return False, "❌ شما قبلاً یک کد دعوت استفاده کرده‌اید!"

    # فقط کاربرانی که کمتر از ۳ میو داشته باشند (تازه‌کار) می‌توانند کد ثبت کنند
    if new_user_data.get('meow_count', 0) > 2:
        return False, "❌ شما بیش از ۲ میو کرده‌اید و نمی‌توانید کد دعوت ثبت کنید!"

    # دریافت اطلاعات دعوت‌کننده
    referrer_data = db.get_key(referrer_id, {})
    referrer_level = referrer_data.get('meow_level', 1)
    reward_type = ""

    # اعمال پاداش بر اساس سطح دعوت‌کننده
    if referrer_level > REFERRAL_MIN_LEVEL:
        # سطح بالاتر از ۱۰ → پاداش به کیف پول (تومان)
        referrer_data['wallet_balance'] = referrer_data.get('wallet_balance', 0) + REFERRAL_REWARD_WALLET
        reward_type = f"💰 {REFERRAL_REWARD_WALLET:,} تومان اعتبار کیف پول"
    else:
        # سطح ۱۰ یا کمتر → پاداش میو پوینت
        referrer_data['meow_points'] = referrer_data.get('meow_points', 0) + REFERRAL_REWARD_POINTS
        reward_type = f"🪙 {REFERRAL_REWARD_POINTS:,} میو پوینت"

    db.set_key(referrer_id, referrer_data)

    # ثبت اطلاعات دعوت برای کاربر جدید
    new_user_data['referred_by'] = referrer_id
    new_user_data['referral_used_at'] = time.time()
    db.set_key(new_user_id, new_user_data)

    # ثبت آمار دعوت‌ها
    referral_stats = db.get_key("referral_stats", {})
    referral_stats[referrer_id] = referral_stats.get(referrer_id, 0) + 1
    db.set_key("referral_stats", referral_stats)

    return True, f"✅ کد دعوت با موفقیت ثبت شد! شما {reward_type} دریافت کردید."


def get_invite_stats(user_id: str) -> dict:
    """دریافت آمار دعوت‌های کاربر"""
    referral_stats = db.get_key("referral_stats", {})
    total_invites = referral_stats.get(user_id, 0)
    user_data = db.get_key(user_id, {})
    code = user_data.get('invite_code')
    return {
        'code': code,
        'total_invites': total_invites,
        'can_generate': user_data.get('meow_level', 1) >= REFERRAL_MIN_LEVEL
    }


def get_referral_leaderboard(limit=10):
    """دریافت لیدربرد دعوت‌کنندگان"""
    referral_stats = db.get_key("referral_stats", {})
    sorted_stats = sorted(referral_stats.items(), key=lambda x: x[1], reverse=True)
    return sorted_stats[:limit]