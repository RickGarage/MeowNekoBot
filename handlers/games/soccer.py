# handlers/games/soccer.py
"""بازی شرط‌بندی فوتبال"""

import time
import random

from config import GAMELS_MIN_USER_LEVEL

from core.db_instance import db
from core.helpers import check_user_registered, format_time, get_user_display_name
from core.roles import get_user_role,VALID_ROLES

STATS_KEYWORDS = ["soccer stats", "stats soccer", "آمار فوتبال", "فوتبال آمار"]
LEADERBOARD_KEYWORDS = ["soccer leaderboard", "soccer top", "لیدربرد فوتبال", "تاپ فوتبال"]

MEDALS = ["🥇", "🥈", "🥉", "🎖", "🏅"]
TITLES = ["پادشاه فوتبال", "ستاره فوتبال", "مهاجم برتر", "هافبک طلایی", "مدافع قهار"]

WIN_MESSAGES = [
    "🎉 گل شد! برد عالی!",
    "⚽️ گوووووول! بردی!",
    "🔥 چه شوتی! گل زیبایی بود!",
    "🌟 سوپر استار! برد کردی!",
    "💪 عالی بود! گل شد!"
]

LOSS_MESSAGES = [
    "😢 تیر به تیر خورد! باختی!",
    "😅 گل نشد! دفعه بعد بهتر شانس بیار!",
    "🤷‍♂️ بدشانس بودی! بازم تلاش کن!",
    "💔 آفساید! گل مردود شد!",
    "😐 فرصت رو از دست دادی!"
]


def handle_soccer(text, sender_id, message_id, chat_id, bot) -> bool:
    if not (text.lower().startswith("soccer") or text.lower().startswith("فوتبال")):
        return False

    # بررسی ثبت نام کاربر
    if not check_user_registered(sender_id, chat_id, bot):
        return True

    # دریافت اطلاعات کاربر
    # دریافت اطلاعات کاربر
    user_data = db.get_key(sender_id, {})

    if not user_data:
            bot.sendMessage(
                chat_id,
                "❌ شما در دیتابیس ثبت نام نشده‌اید! لطفاً ربات را در پیوی استارت کنید.",
                reply_to_message_id=message_id
            )
            return True

    # کاربر پیشی نداره -> شروع فرآیند خرید
    user_level = user_data.get('meow_level', 1)

    if user_level < GAMELS_MIN_USER_LEVEL:
        bot.sendMessage(
            chat_id,
            f"🔒 برای شرطبندی باید حداقل سطح {GAMELS_MIN_USER_LEVEL} باشی!\n"
            f"⭐️ سطح فعلی تو : {user_level}",
            reply_to_message_id=message_id
        )
        return True

    # بررسی کول‌داون (2 دقیقه = 120 ثانیه)
    last_soccer = user_data.get('last_soccer', 0)
    current_time = time.time()
    user_role = get_user_role(sender_id)
    
    if user_role == VALID_ROLES[2]:
        cooldown_seconds = 30
    elif user_role == VALID_ROLES[3]:
        cooldown_seconds = 0
    else:
        cooldown_seconds = 120

    if current_time - last_soccer < cooldown_seconds:
        remaining = int(cooldown_seconds - (current_time - last_soccer))
        formatted_time = format_time(remaining)
        bot.sendMessage(
            chat_id,
            f"⏳ هنوز زمان شرط‌بندی تموم نشده!\n"
            f"باید {formatted_time} صبر کنی تا دوباره بتونی شرط ببندی.",
            reply_to_message_id=message_id
        )
        return True

    # استخراج مقدار شرط
    text_parts = text.split()
    if len(text_parts) < 2:
        bot.sendMessage(
            chat_id,
            "⚽️ برای شرط‌بندی باید مقدار پوینت رو وارد کنی!\n"
            "مثال: soccer 100\n"
            "محدوده: 10 تا 50000 پوینت",
            reply_to_message_id=message_id
        )
        return True

    try:
        bet_amount = int(text_parts[1])
    except ValueError:
        bot.sendMessage(
            chat_id,
            "❌ مقدار وارد شده معتبر نیست! لطفاً یک عدد وارد کن.",
            reply_to_message_id=message_id
        )
        return True

    # بررسی محدوده شرط
    if bet_amount < 10 or bet_amount > 50000:
        bot.sendMessage(
            chat_id,
            "❌ مقدار شرط باید بین 10 تا 50000 باشد!",
            reply_to_message_id=message_id
        )
        return True

    user_points = user_data.get('meow_points', 0)

    # بررسی موجودی کاربر
    if bet_amount > user_points:
        bot.sendMessage(
            chat_id,
            f"❌ پوینت کافی نداری!\n"
            f"💰 پوینت شما: {user_points:,}\n"
            f"📤 پوینت مورد نیاز: {bet_amount:,}",
            reply_to_message_id=message_id
        )
        return True

    # دریافت سطح کاربر برای محاسبه ضریب
    user_level = user_data.get('meow_level', 1)

    # ضریب شانسی با احتساب سطح کاربر
    max_multiplier = min(user_level, 10)  # حداکثر ضریب 10
    min_multiplier = 0.5

    # شانس ضریب‌های بالا کمتر است
    if random.random() < 0.3:  # 30% شانس ضریب پایین
        multiplier = round(random.uniform(min_multiplier, 2), 1)
    elif random.random() < 0.6:  # 30% شانس ضریب متوسط
        multiplier = round(random.uniform(2, 5), 1)
    else:  # 40% شانس ضریب بالا
        multiplier = round(random.uniform(5, max_multiplier), 1)

    # اطمینان از اینکه ضریب از max_multiplier بیشتر نباشد
    multiplier = min(multiplier, max_multiplier)

    # تعیین نتیجه (شانسی) - 40% شانس باخت، 60% شانس برد
    is_win = random.random() < 0.6

    win_amount = 0

    # محاسبه نتیجه
    if is_win:
        # محاسبه پوینت برد (ضریب * مبلغ شرط)
        win_amount = int(bet_amount * multiplier)

        # بروزرسانی پوینت کاربر
        user_data['meow_points'] = user_points + win_amount
        user_data['last_soccer'] = current_time
        user_data['soccer_wins'] = user_data.get('soccer_wins', 0) + 1
        user_data['soccer_total_bets'] = user_data.get('soccer_total_bets', 0) + 1
        user_data['soccer_total_won'] = user_data.get('soccer_total_won', 0) + win_amount

        # ذخیره در دیتابیس
        db.set_key(sender_id, user_data)

        bot.sendMessage(
            chat_id,
            f"⚽️ شرط‌بندی فوتبال!\n\n"
            f"{random.choice(WIN_MESSAGES)}\n"
            f"💰 مبلغ شرط: {bet_amount:,} پوینت\n"
            f"🎯 ضریب: {multiplier}x\n"
            f"🏆 برد شما: {win_amount:,} پوینت\n"
            f"📊 موجودی جدید: {user_data['meow_points']:,} پوینت\n\n"
            f"📈 آمار شرط‌بندی:\n"
            f"┐─ ✅ بردها: {user_data['soccer_wins']}\n"
            f"┘─ 💰 کل برد: {user_data['soccer_total_won']:,} پوینت",
            reply_to_message_id=message_id
        )
    else:
        # باخت
        user_data['meow_points'] = user_points - bet_amount
        user_data['last_soccer'] = current_time
        user_data['soccer_losses'] = user_data.get('soccer_losses', 0) + 1
        user_data['soccer_total_bets'] = user_data.get('soccer_total_bets', 0) + 1

        # ذخیره در دیتابیس
        db.set_key(sender_id, user_data)

        bot.sendMessage(
            chat_id,
            f"⚽️ شرط‌بندی فوتبال!\n\n"
            f"{random.choice(LOSS_MESSAGES)}\n"
            f"💰 مبلغ شرط: {bet_amount:,} پوینت\n"
            f"🎯 ضریب: {multiplier}x\n"
            f"📊 موجودی جدید: {user_data['meow_points']:,} پوینت\n\n"
            f"📈 آمار شرط‌بندی:\n"
            f"┐─ ❌ باخت‌ها: {user_data['soccer_losses']}\n"
            f"┘─ 📉 کل باخت: {bet_amount:,} پوینت",
            reply_to_message_id=message_id
        )

    # ثبت تاریخچه شرط‌بندی
    soccer_history = db.get_key("soccer_history", [])
    soccer_history.append({
        'user_id': sender_id,
        'bet': bet_amount,
        'multiplier': multiplier,
        'result': 'win' if is_win else 'loss',
        'win_amount': win_amount if is_win else 0,
        'time': current_time
    })
    # نگهداری فقط 200 تاریخچه آخر
    if len(soccer_history) > 200:
        soccer_history = soccer_history[-200:]
    db.set_key("soccer_history", soccer_history)

    return True


def handle_soccer_stats(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.lower() not in STATS_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    user_data = db.get_key(sender_id, {})
    if not user_data:
        bot.sendMessage(
            chat_id,
            "❌ شما در دیتابیس ثبت نام نشده‌اید!",
            reply_to_message_id=message_id
        )
        return True

    total_bets = user_data.get('soccer_total_bets', 0)
    wins = user_data.get('soccer_wins', 0)
    losses = user_data.get('soccer_losses', 0)
    total_won = user_data.get('soccer_total_won', 0)

    # محاسبه درصد برد
    win_rate = (wins / total_bets * 100) if total_bets > 0 else 0

    bot.sendMessage(
        chat_id,
        f"⚽️ آمار شرط‌بندی فوتبال شما:\n\n"
        f"📊 مجموع شرط‌ها: {total_bets}\n"
        f"✅ بردها: {wins}\n"
        f"❌ باخت‌ها: {losses}\n"
        f"🎯 درصد برد: {win_rate:.1f}%\n"
        f"💰 کل برد: {total_won:,} پوینت\n\n"
        f"📈 بهترین ضریب: {user_data.get('soccer_best_multiplier', 0)}x\n"
        f"🔥 بیشترین برد: {user_data.get('soccer_biggest_win', 0):,} پوینت",
        reply_to_message_id=message_id
    )
    return True


def handle_soccer_leaderboard(text, sender_id, message_id, chat_id, bot) -> bool:
    if text.lower() not in LEADERBOARD_KEYWORDS:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    all_users = db.get_all_keys()
    soccer_stats = []

    for uid in all_users:
        if not uid:
            continue
        if uid.startswith('u') or uid.startswith('b'):
            data = db.get_key(uid, {})
            if isinstance(data, list):
                continue
            if data:
                wins = data.get('soccer_wins', 0)
                total_won = data.get('soccer_total_won', 0)
                if wins > 0 or total_won > 0:
                    soccer_stats.append((uid, wins, total_won, data))

    # مرتب‌سازی بر اساس کل برد
    soccer_stats.sort(key=lambda x: x[2], reverse=True)
    top_users = soccer_stats[:5]

    if not top_users:
        bot.sendMessage(
            chat_id,
            "📊 هنوز کسی شرط‌بندی نکرده! اولین نفر باش!",
            reply_to_message_id=message_id
        )
        return True

    message = "⚽️ لیدربرد شرط‌بندی فوتبال 🏆\n\n"
    message += "💰 بر اساس کل برد پوینت\n\n"

    for idx, (uid, wins, total_won, data) in enumerate(top_users):
        # اطمینان از اینکه data دیکشنری است
        if not isinstance(data, dict):
            data = {}

        medal = MEDALS[idx] if idx < len(MEDALS) else f"#{idx+1}"
        title = TITLES[idx] if idx < len(TITLES) else "بازیکن برتر"

        display_name = get_user_display_name(bot, uid)
        total_bets = data.get('soccer_total_bets', 0) if isinstance(data, dict) else 0
        win_rate = (wins / total_bets * 100) if total_bets > 0 else 0

        message += f"{medal} {title} : {display_name}\n"
        message += f"┘─ 💰 کل برد: {total_won:,} پوینت\n"
        message += f"┘─ 🏆 تعداد برد: {wins}\n"
        message += f"┘─ 🎯 درصد برد: {win_rate:.1f}%\n\n"

    # رتبه کاربر
    user_rank = 0
    for idx, (uid, _, _, _) in enumerate(soccer_stats, 1):
        if uid == sender_id:
            user_rank = idx
            break

    if user_rank > 0:
        message += f"🎖️ رتبه شما: #{user_rank:,}\n"
        user_data = db.get_key(sender_id, {})
        message += f"💰 کل برد شما: {user_data.get('soccer_total_won', 0):,} پوینت"

    bot.sendMessage(chat_id, message, reply_to_message_id=message_id)
    return True
