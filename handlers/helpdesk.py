# handlers/helpdesk.py
import time
from core.helpers import check_user_registered, get_user_display_name
from core.ticket import (
    create_ticket, get_ticket, update_ticket, get_user_tickets,
    get_all_tickets, get_helper_stats, get_helper_leaderboard
)
from core.roles import get_user_role
from config import HELP_GROUP_CHAT_ID, ADMIN_ID


def handle_helpme(text: str, sender_id, message_id, chat_id, bot):
    text_parts = text.split()
    if not text_parts[0].lower() in ['ticket', 'تیکت']:
        return False
    
    if chat_id.startswith('g'):
        return True

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    question = text[len(text_parts[0]):].strip()
    if not question:
        bot.sendMessage(chat_id, "❌ لطفاً سوالت رو بنویس!", reply_to_message_id=message_id)
        return True

    ticket_id = create_ticket(sender_id, question, chat_id, message_id)
    user_name = get_user_display_name(bot, sender_id)
    help_msg = (
        f"🆘 درخواست کمک جدید!\n"
        f"👤 کاربر: {user_name}\n"
        f"🆔 کد تیکت: `{ticket_id}`\n"
        f"📝 سوال:\n{question}\n\n"
        f"✅ برای پاسخ از دستور زیر استفاده کن:\n"
        f"`answer {ticket_id}`"
    )
    msg_id = bot.sendMessage(HELP_GROUP_CHAT_ID, help_msg)
    if msg_id:
        bot.sendMessage(
            chat_id,
            f"✅ سوالت ثبت شد! کد تیکت: `{ticket_id}`\nبه زودی پاسخ می‌دیم.",
            reply_to_message_id=message_id
        )
    else:
        bot.sendMessage(
                    chat_id,
                    f"یک مشکل پیش آمده است لطفا صبر کنید بزودی برطرف میشود.",
                    reply_to_message_id=message_id
                )
    return True


def handle_answer_command(text, sender_id, message_id, chat_id, bot):
    """
    کامند پاسخ به تیکت با دستور:
    answer [ticket_id] [متن پاسخ]
    یا
    پاسخ [ticket_id] [متن پاسخ]
    """
    if not text.lower().startswith("answer ") and not text.lower().startswith("پاسخ "):
        return False

    if chat_id != HELP_GROUP_CHAT_ID:
        bot.sendMessage(
            chat_id,
            "❌ این دستور فقط در گروه هلپرها قابل استفاده است!",
            reply_to_message_id=message_id
        )
        return True

    parts = text.split(maxsplit=2)
    if len(parts) < 3:
        bot.sendMessage(
            chat_id,
            "❌ فرمت صحیح:\n`answer [ticket_id] [متن پاسخ]`\nمثال: `answer ABC12345 سلام، میو کن`",
            reply_to_message_id=message_id
        )
        return True

    ticket_id = parts[1].strip()
    answer_text = parts[2].strip()

    if not answer_text:
        bot.sendMessage(chat_id, "❌ متن پاسخ نمی‌تونه خالی باشه!", reply_to_message_id=message_id)
        return True

    ticket = get_ticket(ticket_id)
    if not ticket:
        bot.sendMessage(chat_id, f"❌ تیکتی با کد `{ticket_id}` پیدا نشد!", reply_to_message_id=message_id)
        return True

    if ticket['status'] != 'open':
        bot.sendMessage(
            chat_id,
            f"❌ این تیکت قبلاً پاسخ داده شده یا بسته شده است! وضعیت فعلی: {ticket['status']}",
            reply_to_message_id=message_id
        )
        return True

    helper_name = get_user_display_name(bot, sender_id)
    user_chat_id = ticket['chat_id']
    
    message_id_ticket = ticket['message_id']

    bot.sendMessage(
        user_chat_id,
        f"📩 پاسخ هلپر `{helper_name}` به سوال شما:\n\n{answer_text}\n\n"
        f"🆔 کد تیکت: `{ticket_id}`\n"
        f"⭐️ اگر پاسخ مفید بود، با دستور `rate {ticket_id} [1-5]` امتیاز بدید.",
        message_id_ticket
    )

    update_ticket(
        ticket_id,
        status='answered',
        helper_id=sender_id,
        helper_message_id=message_id,
        answered_at=time.time()
    )

    bot.sendMessage(
        chat_id,
        f"✅ پاسخ شما به کاربر ارسال شد. تیکت `{ticket_id}` بسته شد.",
        reply_to_message_id=message_id
    )
    return True


def handle_rate_ticket(text, sender_id, message_id, chat_id, bot):
    if not text.lower().startswith("rate "):
        return False

    parts = text.split()
    if len(parts) < 3:
        bot.sendMessage(chat_id, "❌ فرمت: rate [تیکت‌آیدی] [امتیاز ۱ تا ۵]", reply_to_message_id=message_id)
        return True

    ticket_id = parts[1]
    try:
        rating = int(parts[2])
        if rating < 1 or rating > 5:
            raise ValueError
    except ValueError:
        bot.sendMessage(chat_id, "❌ امتیاز باید عددی بین ۱ تا ۵ باشد!", reply_to_message_id=message_id)
        return True

    ticket = get_ticket(ticket_id)
    if not ticket:
        bot.sendMessage(chat_id, "❌ تیکت یافت نشد!", reply_to_message_id=message_id)
        return True

    if ticket['user_id'] != sender_id:
        bot.sendMessage(chat_id, "❌ این تیکت متعلق به شما نیست!", reply_to_message_id=message_id)
        return True

    if ticket['status'] not in ['answered', 'closed']:
        bot.sendMessage(chat_id, "❌ این تیکت هنوز پاسخ داده نشده!", reply_to_message_id=message_id)
        return True

    if ticket.get('rating'):
        bot.sendMessage(chat_id, "❌ شما قبلاً به این تیکت امتیاز داده‌اید!", reply_to_message_id=message_id)
        return True

    update_ticket(ticket_id, rating=rating, status='closed', closed_at=time.time())
    bot.sendMessage(chat_id, f"✅ امتیاز شما ثبت شد! ممنون از نظرتون.", reply_to_message_id=message_id)
    return True


def handle_my_tickets(text, sender_id, message_id, chat_id, bot):
    if text.strip().lower() not in ['myhelps', 'تیکتهام', 'mytickets']:
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    tickets = get_user_tickets(sender_id)
    if not tickets:
        bot.sendMessage(chat_id, "📭 شما هیچ تیکتی ثبت نکردید.", reply_to_message_id=message_id)
        return True

    msg = "📋 لیست تیکت‌های شما:\n\n"
    status_map = {
        'open': '⏳ در انتظار پاسخ',
        'answered': '✅ پاسخ داده شده',
        'closed': '🔒 بسته شده'
    }
    for t in tickets:
        status_text = status_map.get(t['status'], t['status'])
        msg += f"┘─ `{t['ticket_id']}` | {status_text}\n   📝 {t['question'][:50]}...\n"

    bot.sendMessage(chat_id, msg, reply_to_message_id=message_id)
    return True


def handle_helper_stats(text, sender_id, message_id, chat_id, bot):
    if not text.lower().startswith("helperstats"):
        return False

    if sender_id not in ADMIN_ID:
        bot.sendMessage(chat_id, "🚫 این کامند فقط برای ادمین است!", reply_to_message_id=message_id)
        return True

    parts = text.split()
    if len(parts) > 1:
        helper_id = parts[1]
        stats = get_helper_stats(helper_id)
        if stats['total_answered'] == 0:
            bot.sendMessage(chat_id, f"📊 هلپر {helper_id} هنوز پاسخی نداده.", reply_to_message_id=message_id)
        else:
            msg = (
                f"📊 آمار هلپر `{helper_id}`:\n"
                f"┘─ تعداد پاسخ‌ها: {stats['total_answered']}\n"
                f"┘─ میانگین امتیاز: {stats['avg_rating']:.2f} (از {stats['count_rated']} نظر)"
            )
            bot.sendMessage(chat_id, msg, reply_to_message_id=message_id)
    else:
        leaderboard = get_helper_leaderboard()
        if not leaderboard:
            bot.sendMessage(chat_id, "📊 هیچ هلپری فعالیت نداشته.", reply_to_message_id=message_id)
            return True

        msg = "📊 **لیدربرد هلپرها**\n\n"
        for idx, h in enumerate(leaderboard[:10], 1):
            msg += f"{idx}. `{get_user_display_name(bot,h['helper_id'])}`\n   ┘─ پاسخ‌ها: {h['answered']} | میانگین امتیاز: {h['avg_rating']:.2f}\n"

        bot.sendMessage(chat_id, msg, reply_to_message_id=message_id)

    return True


def handle_helper_leaderboard(text, sender_id, message_id, chat_id, bot):
    if not text.lower().startswith("helperleaderboard") and text not in ["لیدربرد هلپر", "helper leaderboard"]:
        return False

    if sender_id not in ADMIN_ID:
        bot.sendMessage(chat_id, "🚫 این کامند فقط برای ادمین است!", reply_to_message_id=message_id)
        return True

    leaderboard = get_helper_leaderboard()
    if not leaderboard:
        bot.sendMessage(chat_id, "📊 هیچ هلپری فعالیت نداشته.", reply_to_message_id=message_id)
        return True

    msg = "🏆 **لیدربرد هلپرها**\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for idx, h in enumerate(leaderboard[:10], 1):
        medal = medals[idx - 1] if idx <= 3 else f"#{idx}"
        msg += f"{medal} `{get_user_display_name(bot,h['helper_id'])}`\n   ┘─ پاسخ‌ها: {h['answered']} | میانگین امتیاز: {h['avg_rating']:.2f}\n"

    bot.sendMessage(chat_id, msg, reply_to_message_id=message_id)
    return True