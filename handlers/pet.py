# handlers/pet.py
"""هندلرهای سیستم پیشی (Pet) - خرید، وضعیت، تغذیه، برداشت، ارتقا سطح/مقام و نام‌گذاری"""

import time

from config import PET_PRICE, PET_MIN_USER_LEVEL, PET_FEED_ENERGY_SECONDS
from core.db_instance import db
from core.helpers import check_user_registered, format_time
from core.conversations import (
    start_conversation,
    get_conversation,
    clear_conversation,
    is_in_conversation,
)
from core.pet_engine import (
    has_pet,
    update_pet_production,
    get_rate_per_sec,
    get_capacity,
    get_level_cap,
    get_upgrade_cost,
    get_rankup_cost,
    get_max_banked_energy,
    is_fed,
    buy_pet,
    collect_pet_points,
    feed_pet,
    upgrade_pet_level,
    rankup_pet,
    rename_pet,
)

PET_KEYWORDS = ["پیشی", "pet"]
FEED_KEYWORDS = ["غذا پیشی", "تغذیه پیشی", "غذا دادن به پیشی"]
COLLECT_KEYWORDS = ["برداشت پیشی", "جمع پوینت پیشی", "جعبه پیشی"]
UPGRADE_KEYWORDS = ["ارتقا سطح پیشی", "ارتقا پیشی"]
RANKUP_KEYWORDS = ["ارتقا مقام پیشی", "ارتقا مقام"]
RENAME_PREFIX = "اسم پیشی "

BUY_CONVERSATION_NAME = "pet_buy"
CONFIRM_YES = ["بله", "اره", "آره", "yes", "y"]
CONFIRM_NO = ["خیر", "نه", "no", "n", "لغو"]


def _format_energy_status(pet, now=None):
    now = now or time.time()
    if is_fed(pet, now):
        remaining = int(pet.get('energy_until', 0) - now)
        return f"🍖 سیره (تا {format_time(remaining)} دیگه انرژی داره)"
    return "🍖 گشنشه! (تولید متوقفه، باهاش ماهی بده)"


def _pet_status_message(pet):
    pet = update_pet_production(pet)

    name = pet.get('name') or "پیشی"
    level = pet.get('level', 1)
    rank = pet.get('rank', 1)
    box_points = int(pet.get('box_points', 0))
    capacity = int(get_capacity(pet))
    rate = get_rate_per_sec(pet)
    level_cap = get_level_cap(pet)
    upgrade_cost = get_upgrade_cost(pet)

    message = f"🐈 {name} 🐾\n\n"
    message += f"⭐️ سطح : {level} / {level_cap} (مقام {rank})\n"
    message += f"⚡️ سرعت تولید : {rate:.1f} میو پوینت در ثانیه\n"
    message += f"📦 جعبه : {box_points:,} / {capacity:,} 🪙\n"
    message += f"{_format_energy_status(pet)}\n\n"

    if box_points > 0:
        message += "👉 برای برداشت پوینت‌ها بگو «برداشت پیشی»\n"
    if level < level_cap:
        message += f"👉 ارتقا سطح : {upgrade_cost:,} پوینت (بگو «ارتقا سطح پیشی»)\n"
    else:
        rankup_cost = get_rankup_cost(pet)
        message += f"🌟 پیشیت آماده «ارتقا مقام»ـه! هزینه : {rankup_cost:,} پوینت\n"
        message += "⚠️ توجه: با ارتقا مقام، سطح و جعبه پیشی صفر میشه اما سقف سطح و ظرفیت شکمش بیشتر میشه.\n"

    return pet, message


def handle_pet(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.lower() not in [k.lower() for k in PET_KEYWORDS]:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})

    if has_pet(user_data):
        pet, message = _pet_status_message(user_data['pet'])
        user_data['pet'] = pet
        db.set_key(sender_id, user_data)
        bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
        return True

    # کاربر پیشی نداره -> شروع فرآیند خرید
    user_level = user_data.get('meow_level', 1)
    user_points = user_data.get('meow_points', 0)

    if user_level < PET_MIN_USER_LEVEL:
        bot.sendMessage(
            chat_id,
            f"🔒 برای خرید پیشی باید حداقل سطح {PET_MIN_USER_LEVEL} باشی!\n"
            f"⭐️ سطح فعلی تو : {user_level}",
            reply_to_message_id=message_id
        )
        return True

    if user_points < PET_PRICE:
        bot.sendMessage(
            chat_id,
            f"💰 برای خرید پیشی به {PET_PRICE:,} میو پوینت نیاز داری!\n"
            f"📊 موجودی فعلی تو : {user_points:,}",
            reply_to_message_id=message_id
        )
        return True

    start_conversation(sender_id, BUY_CONVERSATION_NAME, step='confirm')
    bot.sendMessage(
        chat_id,
        f"🐈 وقتشه صاحب یه پیشی اختصاصی بشی!\n\n"
        f"💰 هزینه : {PET_PRICE:,} میو پوینت\n"
        f"📊 موجودی تو : {user_points:,} میو پوینت\n\n"
        f"مطمئنی میخوای بخریش؟ («بله» یا «خیر»)",
        reply_to_message_id=message_id
    )
    return True


def handle_pet_buy_conversation(text, sender_id, message_id, chat_id, bot) -> bool:
    conv = get_conversation(sender_id)
    if not conv or conv.get('name') != BUY_CONVERSATION_NAME:
        return False

    choice = text.strip().lower()

    if choice in CONFIRM_NO:
        clear_conversation(sender_id)
        bot.sendMessage(chat_id, "❌ خرید پیشی لغو شد.", reply_to_message_id=message_id)
        return True

    if choice not in CONFIRM_YES:
        bot.sendMessage(
            chat_id,
            "❓ لطفاً «بله» یا «خیر» رو بفرست.",
            reply_to_message_id=message_id
        )
        return True

    clear_conversation(sender_id)

    user_data = db.get_key(sender_id, {})
    success, reason = buy_pet(sender_id, user_data)

    if not success:
        error_messages = {
            'already_has_pet': "🐈 تو همین الانم یه پیشی داری!",
            'level_too_low': f"🔒 برای خرید پیشی باید حداقل سطح {PET_MIN_USER_LEVEL} باشی!",
            'not_enough_points': f"💰 پوینت کافی نداری! (هزینه: {PET_PRICE:,} پوینت)",
        }
        bot.sendMessage(
            chat_id,
            error_messages.get(reason, "❌ مشکلی پیش اومد!"),
            reply_to_message_id=message_id
        )
        return True

    bot.sendMessage(
        chat_id,
        f"🎉 تبریک! صاحب یه پیشی جدید شدی 🐈\n\n"
        f"💫 پیشیت از همین الان شروع به تولید میو پوینت میکنه!\n"
        f"🍖 یادت نره غذاش بدی وگرنه گشنه میمونه و تولید متوقف میشه.\n"
        f"👉 برای دیدن وضعیتش بگو «پیشی»\n"
        f"👉 برای اسم گذاشتن بگو «اسم پیشی [نام دلخواه]»",
        reply_to_message_id=message_id
    )
    return True


def handle_feed_pet(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.lower() not in [k.lower() for k in FEED_KEYWORDS]:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    success, reason, fish_name = feed_pet(sender_id, user_data)

    if not success:
        error_messages = {
            'no_pet': "🐈 هنوز پیشی نداری! بگو «پیشی» تا یکی بخری.",
            'no_fish': "🐟 توی انبارت هیچ ماهی‌ای نداری! برو یه دستی ماهیگیری کن 🎣",
            'energy_full': "🍖 پیشیت الان کاملاً سیره، نیازی به غذای بیشتر نداره!",
        }
        db.set_key(sender_id, user_data)
        bot.sendMessage(
            chat_id,
            error_messages.get(reason, "❌ مشکلی پیش اومد!"),
            reply_to_message_id=message_id
        )
        return True

    bot.sendMessage(
        chat_id,
        f"😻 پیشیت با اشتها {fish_name} رو خورد!\n"
        f"⚡️ {PET_FEED_ENERGY_SECONDS // 3600} ساعت بهش انرژی اضافه شد.",
        reply_to_message_id=message_id
    )
    return True


def handle_collect_pet(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.lower() not in [k.lower() for k in COLLECT_KEYWORDS]:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    if not has_pet(user_data):
        bot.sendMessage(chat_id, "🐈 هنوز پیشی نداری! بگو «پیشی» تا یکی بخری.", reply_to_message_id=message_id)
        return True

    collected, user_data = collect_pet_points(sender_id, user_data)

    if collected <= 0:
        bot.sendMessage(
            chat_id,
            "📦 جعبه پیشیت خالیه! یکم صبر کن تا پوینت جمع کنه.",
            reply_to_message_id=message_id
        )
        return True

    bot.sendMessage(
        chat_id,
        f"✅ {collected:,} میو پوینت از جعبه پیشیت برداشت شد!\n"
        f"📊 موجودی جدید : {user_data.get('meow_points', 0):,} پوینت",
        reply_to_message_id=message_id
    )
    return True


def handle_upgrade_pet(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.lower() not in [k.lower() for k in UPGRADE_KEYWORDS]:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    if not has_pet(user_data):
        bot.sendMessage(chat_id, "🐈 هنوز پیشی نداری! بگو «پیشی» تا یکی بخری.", reply_to_message_id=message_id)
        return True

    success, reason, cost = upgrade_pet_level(sender_id, user_data)

    if not success:
        error_messages = {
            'level_capped': "🌟 پیشیت به سقف سطح این مقام رسیده! برای ادامه باید «ارتقا مقام» بدی.",
            'not_enough_points': f"💰 پوینت کافی نداری! (هزینه: {cost:,} پوینت)",
        }
        bot.sendMessage(
            chat_id,
            error_messages.get(reason, "❌ مشکلی پیش اومد!"),
            reply_to_message_id=message_id
        )
        return True

    pet = user_data['pet']
    bot.sendMessage(
        chat_id,
        f"🎉 پیشیت به سطح {pet['level']} ارتقا پیدا کرد!\n"
        f"💰 هزینه پرداختی : {cost:,} پوینت\n"
        f"⚡️ سرعت تولید جدید : {get_rate_per_sec(pet):.1f} پوینت در ثانیه\n"
        f"📦 ظرفیت جدید جعبه : {int(get_capacity(pet)):,} پوینت",
        reply_to_message_id=message_id
    )
    return True


def handle_rankup_pet(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.lower() not in [k.lower() for k in RANKUP_KEYWORDS]:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    if not has_pet(user_data):
        bot.sendMessage(chat_id, "🐈 هنوز پیشی نداری! بگو «پیشی» تا یکی بخری.", reply_to_message_id=message_id)
        return True

    success, reason, cost = rankup_pet(sender_id, user_data)

    if not success:
        error_messages = {
            'level_not_maxed': "🔒 پیشیت هنوز به سقف سطح این مقام نرسیده!",
            'not_enough_points': f"💰 پوینت کافی نداری! (هزینه: {cost:,} پوینت)",
        }
        bot.sendMessage(
            chat_id,
            error_messages.get(reason, "❌ مشکلی پیش اومد!"),
            reply_to_message_id=message_id
        )
        return True

    pet = user_data['pet']
    bot.sendMessage(
        chat_id,
        f"🌟 تبریک! پیشیت به مقام {pet['rank']} ارتقا پیدا کرد!\n\n"
        f"💰 هزینه پرداختی : {cost:,} پوینت\n"
        f"⭐️ سطح و جعبه پیشی صفر شد\n"
        f"⬆️ سقف سطح جدید : {get_level_cap(pet)}\n"
        f"🍖 ظرفیت شکم جدید : {get_max_banked_energy(pet) // 3600} ساعت",
        reply_to_message_id=message_id
    )
    return True


def handle_rename_pet(text, sender_id, message_id, chat_id, bot) -> bool:
    if not text.startswith(RENAME_PREFIX):
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    new_name = text[len(RENAME_PREFIX):].strip()

    if not new_name:
        bot.sendMessage(
            chat_id,
            "❌ اسم نمیتونه خالی باشه!\nمثال: اسم پیشی ملوسک",
            reply_to_message_id=message_id
        )
        return True

    if len(new_name) > 20:
        bot.sendMessage(chat_id, "❌ اسم نباید بیشتر از 20 کاراکتر باشه!", reply_to_message_id=message_id)
        return True

    user_data = db.get_key(sender_id, {})
    if not has_pet(user_data):
        bot.sendMessage(chat_id, "🐈 هنوز پیشی نداری! بگو «پیشی» تا یکی بخری.", reply_to_message_id=message_id)
        return True

    rename_pet(sender_id, user_data, new_name)
    bot.sendMessage(
        chat_id,
        f"💕 از این به بعد پیشیت «{new_name}» صدا زده میشه!",
        reply_to_message_id=message_id
    )
    return True
