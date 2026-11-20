# handlers/street_cats.py
"""هندلر پیشی‌های خیابونی - ظاهر شدن تصادفی در گروه و تلاش برای نجات"""

from core.db_instance import db
from core.helpers import check_user_registered, format_time, get_user_display_name
from core.street_cats import (
    maybe_spawn_event,
    attempt_rescue,
    check_and_expire,
    attempt_cost,
    MAX_ATTEMPTS,
    SUCCESS_CHANCE,
)

RESCUE_KEYWORDS = ["نجات پیشی", "کمک پیشی", "save cat"]
KINDNESS_LEADERBOARD_KEYWORDS = ["لیدربرد مهربونی", "لیدربرد نجات", "مهربون ترین پیشی ها"]

MEDALS = ["🥇", "🥈", "🥉", "🎖", "🏅"]


def try_spawn_street_cat(chat_type, chat_id, bot):
    """
    باید بعد از هر «میو» موفق در یک گروه فراخوانی بشه. با احتمالی متناسب با سطح شهر،
    ممکنه یه پیشی خیابونی جدید ظاهر بشه و پیام اعلانش رو در گروه بفرسته.
    """
    if chat_type not in ("Group", "SuperGroup"):
        return

    event = maybe_spawn_event(chat_id, bot)
    if not event:
        return

    first_cost = attempt_cost(0)
    bot.sendMessage(
        chat_id,
        f"😿 یه پیشی خیابونی ترسیده همین الان تو کوچه‌ های شهرتون ظاهر شد!\n\n"
        f"🐾 صداش می‌لرزه... انگار به کمک نیاز داره.\n"
        f"┘─ 🍀 شما و بقیه اهالی شهر کلا {MAX_ATTEMPTS} تا فرصت دارید نجاتش بدید\n"
        f"┘─ 🎲 شانس موفقیت هر تلاش: {int(SUCCESS_CHANCE * 100)}٪\n"
        f"┘─ 💰 هزینه اولین تلاش: {first_cost:,} پوینت (بعد از هر شکست گرون‌تر میشه!)\n"
        f"┘─ ⌛️ فقط {format_time(300)} فرصت دارید وگرنه برای همیشه میره\n\n"
        f"برای تلاش برای نجاتش بگو «نجات پیشی» 🐈"
    )


def handle_rescue_attempt(text, chat_type, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in RESCUE_KEYWORDS:
        return False

    if chat_type not in ("Group", "SuperGroup"):
        bot.sendMessage(chat_id, "🐾 این دستور فقط داخل گروه‌ ها کار می‌کنه!", reply_to_message_id=message_id)
        return True

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    # چک کردن انقضا قبل از تلاش (برای پیام درست به کاربر)
    if check_and_expire(chat_id):
        bot.sendMessage(
            chat_id,
            "😢 دیر رسیدی... اون پیشی خیابونی ناامید شد و برای همیشه از اینجا رفت.",
            reply_to_message_id=message_id
        )
        return True

    display_name = get_user_display_name(bot, sender_id)
    result = attempt_rescue(chat_id, sender_id)

    outcome = result['result']

    if outcome == 'no_event':
        bot.sendMessage(
            chat_id,
            "🐾 الان هیچ پیشی خیابونی‌ای منتظر کمک نیست!",
            reply_to_message_id=message_id
        )
        return True

    if outcome == 'not_enough_points':
        bot.sendMessage(
            chat_id,
            f"❌ پوینت کافی برای این تلاش نداری!\n💰 هزینه لازم: {result['cost']:,} پوینت",
            reply_to_message_id=message_id
        )
        return True

    if outcome == 'success':
        bot.sendMessage(
            chat_id,
            f"🎉 {display_name} موفق شد پیشی خیابونی رو نجات بده! 😻\n\n"
            f"💰 هزینه تلاش: {result['cost']:,} پوینت\n"
            f"🎁 پاداش نجات: {result['reward']:,} پوینت\n"
            f"🐈 مجموع پیشی‌ های نجات‌داده شده توسط {display_name}: {result['total_rescued']:,}\n\n"
            f"💕 اون پیشی با یه میوی بلند ازت تشکر کرد!",
            reply_to_message_id=message_id
        )
        return True

    if outcome == 'fail':
        bot.sendMessage(
            chat_id,
            f"😿 {display_name} تلاش کرد ولی پیشی هنوز می‌ترسه و فرار کرد...\n\n"
            f"💰 هزینه این تلاش: {result['cost']:,} پوینت\n"
            f"🔁 فرصت باقی‌مونده: {result['attempts_left']}\n"
            f"💸 هزینه تلاش بعدی: {result['next_cost']:,} پوینت\n\n"
            f"دوباره امتحان کن! بگو «نجات پیشی»",
            reply_to_message_id=message_id
        )
        return True

    if outcome == 'lost':
        bot.sendMessage(
            chat_id,
            f"💔 {display_name} آخرین تلاش رو هم کرد ولی...\n\n"
            f"💰 هزینه این تلاش: {result['cost']:,} پوینت\n"
            f"⚰️ متاسفانه پیشی خیابونی از دست رفت. شاید دفعه بعد شانس بیاریم...",
            reply_to_message_id=message_id
        )
        return True

    return True


def handle_kindness_leaderboard(text, chat_type, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in KINDNESS_LEADERBOARD_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    all_users = db.get_all_keys()
    kind_users = []

    for uid in all_users:
        if not uid:
            continue
        if uid.startswith('u') or uid.startswith('b'):
            data = db.get_key(uid, {})
            if isinstance(data, dict) and data.get('rescued_cats_count', 0) > 0:
                kind_users.append((uid, data['rescued_cats_count']))

    kind_users.sort(key=lambda x: x[1], reverse=True)
    top_users = kind_users[:5]

    if not top_users:
        bot.sendMessage(
            chat_id,
            "🐈 هنوز هیچ‌ کس پیشی خیابونی‌ای رو نجات نداده! اولین قهرمان مهربون باش 💕",
            reply_to_message_id=message_id
        )
        return True

    message = "💕 لیدربرد مهربون‌ ترین پیشی‌ ها 🐈\n\n"
    for idx, (uid, count) in enumerate(top_users):
        medal = MEDALS[idx] if idx < len(MEDALS) else f"#{idx+1}"
        display_name = get_user_display_name(bot, uid)
        message += f"{medal} {display_name}\n┘─ 🐈 پیشی‌ های نجات‌داده: {count:,}\n\n"

    user_rank = 0
    for idx, (uid, _) in enumerate(kind_users, 1):
        if uid == sender_id:
            user_rank = idx
            break

    if user_rank > 0:
        user_data = db.get_key(sender_id, {})
        message += f"🎖️ رتبه شما: #{user_rank:,}\n"
        message += f"🐈 پیشی‌ های نجات‌داده شما: {user_data.get('rescued_cats_count', 0):,}"
    else:
        message += "🐈 تو هنوز هیچ پیشی‌ ای نجات ندادی! بگو «نجات پیشی» وقتی یکی ظاهر شد."

    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True
