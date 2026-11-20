# handlers/bank.py
"""هندلر بانک میویی - افتتاح حساب، واریز/برداشت، تغییر شماره حساب، کارت‌به‌کارت"""

from core.db_instance import db
from core.helpers import check_user_registered, format_time, get_user_display_name
from config import (
    BANK_MIN_LEVEL,
    BANK_OPEN_COST,
    BANK_CHANGE_NUMBER_COST,
    BANK_DAILY_INTEREST_RATE,
    BANK_MAX_DAILY_INTEREST
)
from core.bank import (
    has_account,
    open_account,
    sync_interest,
    can_change_number,
    change_account_number,
    deposit,
    withdraw,
    calc_transfer_fee,
    get_owner_by_account_number,
)

BANK_ENTRY_KEYWORDS = ["بانک میویی"]
CHANGE_NUMBER_KEYWORDS = ["تغییر شماره حساب"]
DEPOSIT_PREFIX = "واریز "
WITHDRAW_PREFIX = "برداشت "
TRANSFER_PREFIX = "کارت به کارت "


def _no_account_message(user_level):
    return (
        f"🏦 هنوز حساب بانکی نداری!\n\n"
        f"┘─ ⭐️ حداقل سطح لازم: {BANK_MIN_LEVEL} (سطح فعلی شما: {user_level})\n"
        f"┘─ 💰 هزینه افتتاح حساب: {BANK_OPEN_COST:,} پوینت\n\n"
        f"برای افتتاح حساب دوباره بگو «بانک میویی» 🏦"
    )


def handle_bank_entry(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in BANK_ENTRY_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})

    if not has_account(user_data):
        user_level = user_data.get('meow_level', 1)
        user_points = user_data.get('meow_points', 0)

        if user_level < BANK_MIN_LEVEL:
            bot.sendMessage(chat_id, _no_account_message(user_level), reply_to_message_id=message_id)
            return True

        if user_points < BANK_OPEN_COST:
            bot.sendMessage(
                chat_id,
                f"❌ پوینت کافی برای افتتاح حساب نداری!\n"
                f"💰 هزینه: {BANK_OPEN_COST:,} پوینت\n"
                f"📊 موجودی شما: {user_points:,} پوینت",
                reply_to_message_id=message_id
            )
            return True

        user_data['meow_points'] = user_points - BANK_OPEN_COST
        bank = open_account(sender_id, user_data)
        db.set_key(sender_id, user_data)

        bot.sendMessage(
            chat_id,
            f"🎉 حساب بانکی‌ ات با موفقیت باز شد! 🏦\n\n"
            f"💳 شماره حساب: {bank['account_number']}\n"
            f"💰 موجودی: 0 پوینت\n\n"
            f"┘─ «واریز [مقدار]» — واریز به بانک\n"
            f"┘─ «برداشت [مقدار]» — برداشت از بانک\n"
            f"┘─ «کارت به کارت [شماره حساب] [مقدار]» — انتقال به حساب دیگر\n"
            f"┘─ سود روزانه: {int(BANK_DAILY_INTEREST_RATE*100)}٪ (سقف {BANK_MAX_DAILY_INTEREST:,} پوینت در روز)",
            reply_to_message_id=message_id
        )
        return True

    # نمایش وضعیت (حساب از قبل وجود دارد)
    interest = sync_interest(user_data)
    db.set_key(sender_id, user_data)

    bank = user_data['bank']
    interest_msg = f"\n🤑 سود روزانه دریافتی: +{interest:,} پوینت!" if interest > 0 else ""

    bot.sendMessage(
        chat_id,
        f"🏦 حساب بانکی شما\n\n"
        f"💳 شماره حساب: {bank['account_number']}\n"
        f"💰 موجودی: {bank['balance']:,} پوینت\n"
        f"📊 میو پوینت نقدی: {user_data.get('meow_points', 0):,} پوینت"
        f"{interest_msg}\n\n"
        f"┘─ «واریز [مقدار]» / «برداشت [مقدار]»\n"
        f"┘─ «کارت به کارت [شماره حساب] [مقدار]»\n"
        f"┘─ «تغییر شماره حساب»",
        reply_to_message_id=message_id
    )
    return True


def handle_bank_deposit(text, sender_id, message_id, chat_id, bot) -> bool:
    if not text.startswith(DEPOSIT_PREFIX):
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    if not has_account(user_data):
        bot.sendMessage(chat_id, "🏦 اول باید حساب بانکی باز کنی! بگو «بانک میویی»", reply_to_message_id=message_id)
        return True

    raw = text[len(DEPOSIT_PREFIX):].strip()
    if not raw.isdigit():
        bot.sendMessage(chat_id, f"❌ فرمت درست: «{DEPOSIT_PREFIX}[مقدار]»", reply_to_message_id=message_id)
        return True

    amount = int(raw)
    if amount <= 0:
        bot.sendMessage(chat_id, "❌ مقدار باید بیشتر از صفر باشه!", reply_to_message_id=message_id)
        return True

    sync_interest(user_data)

    if user_data.get('meow_points', 0) < amount:
        bot.sendMessage(
            chat_id,
            f"❌ میو پوینت کافی نداری!\n📊 موجودی نقدی: {user_data.get('meow_points', 0):,} پوینت",
            reply_to_message_id=message_id
        )
        db.set_key(sender_id, user_data)
        return True

    user_data = deposit(user_data, amount)
    db.set_key(sender_id, user_data)

    bot.sendMessage(
        chat_id,
        f"✅ {amount:,} پوینت به بانک واریز شد!\n"
        f"💰 موجودی بانک: {user_data['bank']['balance']:,} پوینت\n"
        f"📊 میو پوینت نقدی: {user_data['meow_points']:,} پوینت",
        reply_to_message_id=message_id
    )
    return True


def handle_bank_withdraw(text, sender_id, message_id, chat_id, bot) -> bool:
    if not text.startswith(WITHDRAW_PREFIX):
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    if not has_account(user_data):
        bot.sendMessage(chat_id, "🏦 اول باید حساب بانکی باز کنی! بگو «بانک میویی»", reply_to_message_id=message_id)
        return True

    raw = text[len(WITHDRAW_PREFIX):].strip()
    if not raw.isdigit():
        bot.sendMessage(chat_id, f"❌ فرمت درست: «{WITHDRAW_PREFIX}[مقدار]»", reply_to_message_id=message_id)
        return True

    amount = int(raw)
    if amount <= 0:
        bot.sendMessage(chat_id, "❌ مقدار باید بیشتر از صفر باشه!", reply_to_message_id=message_id)
        return True

    sync_interest(user_data)

    if user_data['bank'].get('balance', 0) < amount:
        bot.sendMessage(
            chat_id,
            f"❌ موجودی بانکت کافی نیست!\n💰 موجودی بانک: {user_data['bank'].get('balance', 0):,} پوینت",
            reply_to_message_id=message_id
        )
        db.set_key(sender_id, user_data)
        return True

    user_data = withdraw(user_data, amount)
    db.set_key(sender_id, user_data)

    bot.sendMessage(
        chat_id,
        f"✅ {amount:,} پوینت از بانک برداشت شد!\n"
        f"💰 موجودی بانک: {user_data['bank']['balance']:,} پوینت\n"
        f"📊 میو پوینت نقدی: {user_data['meow_points']:,} پوینت",
        reply_to_message_id=message_id
    )
    return True


def handle_bank_change_number(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in CHANGE_NUMBER_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    if not has_account(user_data):
        bot.sendMessage(chat_id, "🏦 اول باید حساب بانکی باز کنی! بگو «بانک میویی»", reply_to_message_id=message_id)
        return True

    allowed, remaining = can_change_number(user_data)
    if not allowed:
        bot.sendMessage(
            chat_id,
            f"⏳ این قابلیت هر 72 ساعت یک‌بار در دسترسه!\nباید {format_time(remaining)} دیگه صبر کنی.",
            reply_to_message_id=message_id
        )
        return True

    if user_data.get('meow_points', 0) < BANK_CHANGE_NUMBER_COST:
        bot.sendMessage(
            chat_id,
            f"❌ پوینت کافی نداری!\n💰 هزینه: {BANK_CHANGE_NUMBER_COST:,} پوینت",
            reply_to_message_id=message_id
        )
        return True

    user_data['meow_points'] -= BANK_CHANGE_NUMBER_COST
    new_number = change_account_number(sender_id, user_data)
    db.set_key(sender_id, user_data)

    bot.sendMessage(
        chat_id,
        f"✅ شماره حساب جدیدت: {new_number}\n💰 هزینه پرداختی: {BANK_CHANGE_NUMBER_COST:,} پوینت",
        reply_to_message_id=message_id
    )
    return True


def handle_bank_transfer(text, sender_id, message_id, chat_id, bot) -> bool:
    if not text.startswith(TRANSFER_PREFIX):
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    parts = text[len(TRANSFER_PREFIX):].strip().split()
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        bot.sendMessage(
            chat_id,
            f"❌ فرمت درست: «{TRANSFER_PREFIX}[شماره حساب ۱۲ رقمی] [مقدار]»",
            reply_to_message_id=message_id
        )
        return True

    target_account, raw_amount = parts
    amount = int(raw_amount)

    if len(target_account) != 12:
        bot.sendMessage(chat_id, "❌ شماره حساب باید ۱۲ رقم باشه!", reply_to_message_id=message_id)
        return True

    if amount <= 0:
        bot.sendMessage(chat_id, "❌ مقدار باید بیشتر از صفر باشه!", reply_to_message_id=message_id)
        return True

    user_data = db.get_key(sender_id, {})
    if not has_account(user_data):
        bot.sendMessage(chat_id, "🏦 اول باید حساب بانکی باز کنی! بگو «بانک میویی»", reply_to_message_id=message_id)
        return True

    if target_account == user_data['bank']['account_number']:
        bot.sendMessage(chat_id, "❌ نمیتونی به حساب خودت انتقال بدی!", reply_to_message_id=message_id)
        return True

    receiver_id = get_owner_by_account_number(target_account)
    if not receiver_id:
        bot.sendMessage(chat_id, "❌ حسابی با این شماره پیدا نشد!", reply_to_message_id=message_id)
        return True

    sync_interest(user_data)

    fee = calc_transfer_fee(amount)
    total_deduct = amount + fee

    if user_data['bank'].get('balance', 0) < total_deduct:
        bot.sendMessage(
            chat_id,
            f"❌ موجودی بانکت کافی نیست!\n"
            f"💰 مبلغ: {amount:,} + کارمزد: {fee:,} = {total_deduct:,} پوینت\n"
            f"📊 موجودی بانک شما: {user_data['bank'].get('balance', 0):,} پوینت",
            reply_to_message_id=message_id
        )
        db.set_key(sender_id, user_data)
        return True

    # کسر از حساب فرستنده
    user_data['bank']['balance'] -= total_deduct
    db.set_key(sender_id, user_data)

    # افزایش حساب گیرنده
    receiver_data = db.get_key(receiver_id, {})
    sync_interest(receiver_data)
    receiver_data['bank']['balance'] = receiver_data['bank'].get('balance', 0) + amount
    db.set_key(receiver_id, receiver_data)

    # محاسبه سود کارمزد (ذخیره در بانک مرکزی یا کارمزدها)
    # برای شفافیت، کارمزد را در یک کلید جداگانه ذخیره می‌کنیم (اختیاری)
    bank_fees = db.get_key("bank_fees", 0)
    bank_fees += fee
    db.set_key("bank_fees", bank_fees)

    receiver_name = get_user_display_name(bot, receiver_id)

    bot.sendMessage(
        chat_id,
        f"✅ انتقال موفق!\n\n"
        f"💳 به حساب: {target_account} ({receiver_name})\n"
        f"💰 مبلغ: {amount:,} پوینت\n"
        f"🧾 کارمزد: {fee:,} پوینت\n"
        f"📊 موجودی جدید بانک شما: {user_data['bank']['balance']:,} پوینت",
        reply_to_message_id=message_id
    )
    return True