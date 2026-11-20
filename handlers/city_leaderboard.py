# handlers/city_leaderboard.py
"""هندلر لیدربرد شهرهای پیشی - رقابت گروه‌ ها (سرزمین‌ ها) با هم"""

from core.helpers import check_user_registered
from core.groups import get_user_group
from core.city_leaderboard import get_top_cities, get_city_rank

LOUD_CITY_KEYWORDS = ["لیدربرد شهر صدا", "لیدربرد شهرهای پرسروصدا"]
POPULATION_CITY_KEYWORDS = ["لیدربرد شهر جمعیت", "لیدربرد شهرهای پرجمعیت"]
TREASURY_CITY_KEYWORDS = ["لیدربرد شهر ثروت", "لیدربرد شهرهای ثروتمند"]
FISH_MARKET_KEYWORDS = ["لیدربرد شهر ماهی", "لیدربرد بازار ماهی"]

MEDALS = ["🥇", "🥈", "🥉", "🎖", "🏅"]


def _build_city_leaderboard(sender_id, metric, title, unit_label, value_fmt):
    top_cities = get_top_cities(metric, 5)

    if not top_cities:
        return "🏙 هنوز هیچ سرزمینی رتبه‌ای تو این دسته کسب نکرده!"

    message = f"{title}\n\n"
    for idx, (chat_id, value, stats, city_title) in enumerate(top_cities):
        medal = MEDALS[idx] if idx < len(MEDALS) else f"#{idx+1}"
        message += f"{medal} {city_title}\n"
        message += f"┘─ {unit_label}: {value_fmt(value)} | 👥 اهالی: {stats['member_count']:,}\n\n"

    user_group = get_user_group(sender_id)
    if user_group:
        rank = get_city_rank(user_group, metric)
        if rank:
            message += f"🎖️ رتبه سرزمین شما: #{rank:,}"
        else:
            message += "🎖️ سرزمین شما هنوز رتبه‌ای تو این دسته نداره."
    else:
        message += "💡 برای شرکت سرزمینت در این رقابت، تو یه گروه بگو «پیوستن به گروه»"

    return message


def handle_loud_city_leaderboard(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in LOUD_CITY_KEYWORDS:
        return False
    if not check_user_registered(sender_id, chat_id, bot):
        return True

    message = _build_city_leaderboard(
        sender_id, 'meow_count',
        "🐾 لیدربرد پرسروصداترین شهر پیشی 🏙",
        "🐾 مجموع میو میو",
        lambda v: f"{v:,}"
    )
    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True


def handle_population_city_leaderboard(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in POPULATION_CITY_KEYWORDS:
        return False
    if not check_user_registered(sender_id, chat_id, bot):
        return True

    message = _build_city_leaderboard(
        sender_id, 'population',
        "🐈 لیدربرد پرجمعیت‌ترین شهر پیشی 🏙",
        "🐈 پیشی‌ های خیابونی نجات‌داده",
        lambda v: f"{v:,}"
    )
    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True


def handle_treasury_city_leaderboard(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in TREASURY_CITY_KEYWORDS:
        return False
    if not check_user_registered(sender_id, chat_id, bot):
        return True

    message = _build_city_leaderboard(
        sender_id, 'treasury',
        "🏦 لیدربرد ثروتمندترین شهر پیشی 🏙",
        "🏦 خزانه (مجموع موجودی بانکی)",
        lambda v: f"{v:,} پوینت"
    )
    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True


def handle_fish_market_city_leaderboard(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.strip() not in FISH_MARKET_KEYWORDS:
        return False
    if not check_user_registered(sender_id, chat_id, bot):
        return True

    message = _build_city_leaderboard(
        sender_id, 'fish_total',
        "🎣 لیدربرد بهترین بازار ماهی 🏙",
        "🐟 مجموع ماهی‌ های صید شده",
        lambda v: f"{v:,}"
    )
    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True
