# handlers/smuggling.py
"""هندلر قاچاق میویی - پنل ریسک/پاداش با پیشی‌ های خیابونی"""

import time

from core.db_instance import db
from core.helpers import check_user_registered, format_time
from core.antispam import is_user_banned
from config import SMUGGLING_MIN_LEVEL, SMUGGLING_MIN_CATS, SMUGGLING_MAX_CATS
from core.smuggling import (
    available_cats,
    has_active_mission,
    is_mission_ready,
    mission_duration,
    catch_chance,
    start_mission,
    resolve_mission,
)

ENTRY_KEYWORDS = ["قاچاق میویی"]
START_PREFIX = "شروع قاچاق "


def _locked_message(user_level):
    return (
        f"🥷 هنوز به دنیای قاچاق راه نداری!\n"
        f"⭐️ حداقل سطح لازم: {SMUGGLING_MIN_LEVEL} (سطح فعلی شما: {user_level})"
    )


def handle_smuggling_entry(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in ENTRY_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    user_level = user_data.get('meow_level', 1)

    if user_level < SMUGGLING_MIN_LEVEL:
        bot.sendMessage(chat_id, _locked_message(user_level), reply_to_message_id=message_id)
        return True

    # اگر ماموریت فعال و آماده است، نتیجه رو همینجا اعلام کن
    if has_active_mission(user_data):
        if is_mission_ready(user_data):
            result = resolve_mission(sender_id, user_data)
            db.set_key(sender_id, user_data)

            if result['result'] == 'success':
                bot.sendMessage(
                    chat_id,
                    f"🎉 محموله با موفقیت به مقصد رسید! 🥷\n\n"
                    f"🐈 تعداد پیشی: {result['cat_count']:,}\n"
                    f"💰 دستمزد دریافتی: {result['reward']:,} پوینت\n\n"
                    f"📊 موجودی جدید: {user_data['meow_points']:,} پوینت",
                    reply_to_message_id=message_id
                )
            else:
                bot.sendMessage(
                    chat_id,
                    f"🚨 لو رفتی! پلیس شهر گیرت انداخت...\n\n"
                    f"⛓️ محموله‌ ات ({result['cat_count']:,} پیشی) مصادره شد و هیچ پوینتی نگرفتی!\n"
                    f"🚫 مستقیم فرستاده شدی «زندان میویی» برای {format_time(result['jail_seconds'])}\n\n"
                    f"برای اطلاع از وضعیت بگو «زندان»",
                    reply_to_message_id=message_id
                )
            return True

        smuggling = user_data['smuggling']
        remaining = int(smuggling['ready_at'] - time.time())
        bot.sendMessage(
            chat_id,
            f"🥷 یه محموله در راهه...\n\n"
            f"🐈 تعداد پیشی: {smuggling['cat_count']:,}\n"
            f"⌛️ زمان باقی‌مانده: {format_time(max(0, remaining))}\n\n"
            f"وقتی آماده شد، دوباره بگو «قاچاق میویی» تا نتیجه رو ببینی.",
            reply_to_message_id=message_id
        )
        return True

    # پنل شروع
    available = available_cats(user_data)

    message = "🥷 به دنیای قاچاق میویی خوش اومدی\n\n"
    message += f"🐈 پیشی‌ های خیابونی آزاد شما: {available:,}\n"
    message += f"📦 محموله باید بین {SMUGGLING_MIN_CATS} تا {SMUGGLING_MAX_CATS} پیشی باشه\n\n"

    if available < SMUGGLING_MIN_CATS:
        message += f"❌ حداقل به {SMUGGLING_MIN_CATS} پیشی خیابونی نیاز داری! برو تو گروه‌ ها چندتا نجات بده 🐾"
    else:
        message += "🚨 نکته: هرچی محموله بزرگ‌تر باشه، هم پاداش بیشتره هم ریسک لو رفتن بیشتر!\n\n"
        message += f"برای شروع بگو: «{START_PREFIX}[تعداد]»\n\n"
        message += "مثال قیمت‌ گذاری ریسک:\n"
        for n in (SMUGGLING_MIN_CATS, (SMUGGLING_MIN_CATS + SMUGGLING_MAX_CATS) // 2, SMUGGLING_MAX_CATS):
            message += f"┘─ {n} پیشی: ⌛️ {format_time(mission_duration(n))} | 👮 ریسک {int(catch_chance(n)*100)}٪\n"

    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True


def handle_start_smuggling(text, sender_id, message_id, chat_id, bot) -> bool:
    if not text.startswith(START_PREFIX):
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    user_level = user_data.get('meow_level', 1)

    if user_level < SMUGGLING_MIN_LEVEL:
        bot.sendMessage(chat_id, _locked_message(user_level), reply_to_message_id=message_id)
        return True

    if has_active_mission(user_data):
        bot.sendMessage(chat_id, "❌ همین الان یه محموله در راهه! صبر کن تا برسه.", reply_to_message_id=message_id)
        return True

    raw = text[len(START_PREFIX):].strip()
    if not raw.isdigit():
        bot.sendMessage(
            chat_id,
            f"❌ فرمت درست: «{START_PREFIX}[تعداد بین {SMUGGLING_MIN_CATS} تا {SMUGGLING_MAX_CATS}]»",
            reply_to_message_id=message_id
        )
        return True

    cat_count = int(raw)
    if not (SMUGGLING_MIN_CATS <= cat_count <= SMUGGLING_MAX_CATS):
        bot.sendMessage(
            chat_id,
            f"❌ تعداد باید بین {SMUGGLING_MIN_CATS} تا {SMUGGLING_MAX_CATS} پیشی باشه!",
            reply_to_message_id=message_id
        )
        return True

    available = available_cats(user_data)
    if available < cat_count:
        bot.sendMessage(
            chat_id,
            f"❌ به این تعداد پیشی خیابونی آزاد نداری!\n🐈 موجودی آزاد: {available:,}",
            reply_to_message_id=message_id
        )
        return True

    smuggling = start_mission(user_data, cat_count)
    db.set_key(sender_id, user_data)

    duration = mission_duration(cat_count)
    risk = catch_chance(cat_count)

    bot.sendMessage(
        chat_id,
        f"🥷 محموله راه افتاد!\n\n"
        f"🐈 تعداد پیشی: {cat_count:,}\n"
        f"⌛️ زمان رسیدن: {format_time(duration)}\n"
        f"👮 ریسک لو رفتن: {int(risk*100)}٪\n"
        f"💰 پاداش تخمینی موفقیت: بین {cat_count*12500:,} تا {cat_count*24000:,} پوینت\n\n"
        f"وقتی وقتش شد، بگو «قاچاق میویی» تا نتیجه رو ببینی. موفق باشی! 🍀",
        reply_to_message_id=message_id
    )
    return True
