from core.db_instance import db
from config import ADMIN_ID

from core.helpers import check_user_registered, get_user_display_name

def give_level(text, message, sender_id, message_id, chat_id, bot):
    text_parts = text.split()
    if not text_parts[0].lower() == "glvl":
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    reply_to_message_id = message.get('reply_to_message_id', None)
    if not reply_to_message_id:
        bot.sendMessage(
            chat_id,
            "❌ برای افزایش سطح باید روی پیام کاربر ریپلای کنی!\n"
            "مثال: glvl 5 (روی پیام کاربر ریپلای کن)",
            reply_to_message_id=message_id
        )
        return True

    try:
        replied_message = bot.getMessage(chat_id + reply_to_message_id)
        if not replied_message:
            bot.sendMessage(
                chat_id,
                "❌ پیام مورد نظر پیدا نشد!",
                reply_to_message_id=message_id
            )
            return True
    except Exception:
        bot.sendMessage(
            chat_id,
            "❌ خطا در دریافت پیام ریپلای شده!",
            reply_to_message_id=message_id
        )
        return True

    target_id = replied_message.get('sender_id')
    if not target_id:
        bot.sendMessage(
            chat_id,
            "❌ شناسه کاربر هدف پیدا نشد!",
            reply_to_message_id=message_id
        )
        return True

    user_data = db.get_key(target_id, {})
    if not user_data:
        bot.sendMessage(
            chat_id,
            "❌ کاربر در دیتابیس ثبت نام نشده است! لطفاً ربات را در پیوی استارت کنید.",
            reply_to_message_id=message_id
        )
        return True

    if len(text_parts) < 2:
        bot.sendMessage(
            chat_id,
            "❌ مقدار سطح را وارد کن!\n"
            "مثال: glvl 5",
            reply_to_message_id=message_id
        )
        return True

    try:
        level_amount = int(text_parts[1])
    except ValueError:
        bot.sendMessage(
            chat_id,
            "❌ مقدار وارد شده معتبر نیست! لطفاً یک عدد وارد کن.",
            reply_to_message_id=message_id
        )
        return True

    if level_amount <= 0:
        bot.sendMessage(
            chat_id,
            "❌ مقدار سطح باید بزرگتر از صفر باشد!",
            reply_to_message_id=message_id
        )
        return True

    current_level = user_data.get('meow_level', 1)
    new_level = current_level + level_amount
    user_data['meow_level'] = new_level
    db.set_key(target_id, user_data)

    target_name = get_user_display_name(bot, target_id)

    bot.sendMessage(
        chat_id,
        f"✅ سطح کاربر با موفقیت افزایش یافت!\n\n"
        f"👤 کاربر: {target_name}\n"
        f"🪪 آیدی: {target_id[:12]}...\n"
        f"📈 سطح قبلی: {current_level}\n"
        f"📈 سطح جدید: {new_level}\n"
        f"➕ افزایش: +{level_amount}",
        reply_to_message_id=message_id
    )

    # ارسال پیام به خود کاربر (در صورت وجود chat_id)
    target_chat_id = user_data.get('chat_id')
    if target_chat_id:
        try:
            bot.sendMessage(
                target_chat_id,
                f"🎉 ادمین سطح شما را افزایش داد!\n"
                f"📈 سطح جدید: {new_level}\n"
                f"➕ افزایش: +{level_amount}"
            )
        except Exception:
            pass

    return True

def remove_level(text, message, sender_id, message_id, chat_id, bot):
    """
    هندلر کاهش سطح کاربر (فقط برای ادمین)
    دستور: rlvl [تعداد] (روی پیام کاربر ریپلای کنید)
    مثال: rlvl 3  -> ۳ سطح از کاربر کم می‌کند
    """
    text_parts = text.split()
    if not text_parts[0].lower() == "rlvl":
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    reply_to_message_id = message.get('reply_to_message_id', None)
    if not reply_to_message_id:
        bot.sendMessage(
            chat_id,
            "❌ برای کاهش سطح باید روی پیام کاربر ریپلای کنی!\n"
            "مثال: rlvl 3 (روی پیام کاربر ریپلای کن)",
            reply_to_message_id=message_id
        )
        return True

    try:
        replied_message = bot.getMessage(chat_id + reply_to_message_id)
        if not replied_message:
            bot.sendMessage(
                chat_id,
                "❌ پیام مورد نظر پیدا نشد!",
                reply_to_message_id=message_id
            )
            return True
    except Exception:
        bot.sendMessage(
            chat_id,
            "❌ خطا در دریافت پیام ریپلای شده!",
            reply_to_message_id=message_id
        )
        return True

    target_id = replied_message.get('sender_id')
    if not target_id:
        bot.sendMessage(
            chat_id,
            "❌ شناسه کاربر هدف پیدا نشد!",
            reply_to_message_id=message_id
        )
        return True

    user_data = db.get_key(target_id, {})
    if not user_data:
        bot.sendMessage(
            chat_id,
            "❌ کاربر در دیتابیس ثبت نام نشده است! لطفاً ربات را در پیوی استارت کنید.",
            reply_to_message_id=message_id
        )
        return True

    if len(text_parts) < 2:
        bot.sendMessage(
            chat_id,
            "❌ مقدار سطح را وارد کن!\n"
            "مثال: rlvl 3",
            reply_to_message_id=message_id
        )
        return True

    try:
        level_amount = int(text_parts[1])
    except ValueError:
        bot.sendMessage(
            chat_id,
            "❌ مقدار وارد شده معتبر نیست! لطفاً یک عدد وارد کن.",
            reply_to_message_id=message_id
        )
        return True

    if level_amount <= 0:
        bot.sendMessage(
            chat_id,
            "❌ مقدار کاهش باید بزرگتر از صفر باشد!",
            reply_to_message_id=message_id
        )
        return True

    current_level = user_data.get('meow_level', 1)
    new_level = current_level - level_amount

    # سطح نباید از ۱ کمتر شود
    if new_level < 1:
        new_level = 1
        bot.sendMessage(
            chat_id,
            f"⚠️ سطح کاربر نمی‌تواند کمتر از ۱ باشد، سطح روی ۱ تنظیم شد.",
            reply_to_message_id=message_id
        )

    user_data['meow_level'] = new_level
    db.set_key(target_id, user_data)

    target_name = get_user_display_name(bot, target_id)
    actual_decrease = current_level - new_level

    bot.sendMessage(
        chat_id,
        f"✅ سطح کاربر با موفقیت کاهش یافت!\n\n"
        f"👤 کاربر: {target_name}\n"
        f"🪪 آیدی: {target_id[:12]}...\n"
        f"📈 سطح قبلی: {current_level}\n"
        f"📈 سطح جدید: {new_level}\n"
        f"➖ کاهش: {actual_decrease}",
        reply_to_message_id=message_id
    )

    # ارسال پیام به خود کاربر (در صورت وجود chat_id)
    target_chat_id = user_data.get('chat_id')
    if target_chat_id:
        try:
            bot.sendMessage(
                target_chat_id,
                f"⚠️ ادمین سطح شما را کاهش داد!\n"
                f"📈 سطح جدید: {new_level}\n"
                f"➖ کاهش: {actual_decrease}"
            )
        except Exception:
            pass

    return True


def give_points(text, message, sender_id, message_id, chat_id, bot):
    """
    هندلر افزایش میو پوینت کاربر (فقط برای ادمین)
    دستور: gpoint [تعداد] (روی پیام کاربر ریپلای کنید)
    مثال: gpoint 100  -> ۱۰۰ پوینت به کاربر اضافه می‌کند
    """
    text_parts = text.split()
    if not text_parts[0].lower() == "gpoint":
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    reply_to_message_id = message.get('reply_to_message_id', None)
    if not reply_to_message_id:
        bot.sendMessage(
            chat_id,
            "❌ برای افزایش پوینت باید روی پیام کاربر ریپلای کنی!\n"
            "مثال: gpoint 100 (روی پیام کاربر ریپلای کن)",
            reply_to_message_id=message_id
        )
        return True

    try:
        replied_message = bot.getMessage(chat_id + reply_to_message_id)
        if not replied_message:
            bot.sendMessage(
                chat_id,
                "❌ پیام مورد نظر پیدا نشد!",
                reply_to_message_id=message_id
            )
            return True
    except Exception:
        bot.sendMessage(
            chat_id,
            "❌ خطا در دریافت پیام ریپلای شده!",
            reply_to_message_id=message_id
        )
        return True

    target_id = replied_message.get('sender_id')
    if not target_id:
        bot.sendMessage(
            chat_id,
            "❌ شناسه کاربر هدف پیدا نشد!",
            reply_to_message_id=message_id
        )
        return True

    user_data = db.get_key(target_id, {})
    if not user_data:
        bot.sendMessage(
            chat_id,
            "❌ کاربر در دیتابیس ثبت نام نشده است! لطفاً ربات را در پیوی استارت کنید.",
            reply_to_message_id=message_id
        )
        return True

    if len(text_parts) < 2:
        bot.sendMessage(
            chat_id,
            "❌ مقدار پوینت را وارد کن!\n"
            "مثال: gpoint 100",
            reply_to_message_id=message_id
        )
        return True

    try:
        point_amount = int(text_parts[1])
    except ValueError:
        bot.sendMessage(
            chat_id,
            "❌ مقدار وارد شده معتبر نیست! لطفاً یک عدد وارد کن.",
            reply_to_message_id=message_id
        )
        return True

    if point_amount <= 0:
        bot.sendMessage(
            chat_id,
            "❌ مقدار پوینت باید بزرگتر از صفر باشد!",
            reply_to_message_id=message_id
        )
        return True

    current_points = user_data.get('meow_points', 0)
    new_points = current_points + point_amount
    user_data['meow_points'] = new_points
    db.set_key(target_id, user_data)

    target_name = get_user_display_name(bot, target_id)

    bot.sendMessage(
        chat_id,
        f"✅ پوینت کاربر با موفقیت افزایش یافت!\n\n"
        f"👤 کاربر: {target_name}\n"
        f"🪪 آیدی: {target_id[:12]}...\n"
        f"💰 پوینت قبلی: {current_points:,}\n"
        f"💰 پوینت جدید: {new_points:,}\n"
        f"➕ افزایش: +{point_amount:,}",
        reply_to_message_id=message_id
    )

    # ارسال پیام به خود کاربر (در صورت وجود chat_id)
    target_chat_id = user_data.get('chat_id')
    if target_chat_id:
        try:
            bot.sendMessage(
                target_chat_id,
                f"🎉 ادمین پوینت شما را افزایش داد!\n"
                f"💰 پوینت جدید: {new_points:,}\n"
                f"➕ افزایش: +{point_amount:,}"
            )
        except Exception:
            pass

    return True


def remove_points(text, message, sender_id, message_id, chat_id, bot):
    """
    هندلر کاهش میو پوینت کاربر (فقط برای ادمین)
    دستور: rpoint [تعداد] (روی پیام کاربر ریپلای کنید)
    مثال: rpoint 50  -> ۵۰ پوینت از کاربر کم می‌کند
    """
    text_parts = text.split()
    if not text_parts[0].lower() == "rpoint":
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True


    reply_to_message_id = message.get('reply_to_message_id', None)
    if not reply_to_message_id:
        bot.sendMessage(
            chat_id,
            "❌ برای کاهش پوینت باید روی پیام کاربر ریپلای کنی!\n"
            "مثال: rpoint 50 (روی پیام کاربر ریپلای کن)",
            reply_to_message_id=message_id
        )
        return True

    try:
        replied_message = bot.getMessage(chat_id + reply_to_message_id)
        if not replied_message:
            bot.sendMessage(
                chat_id,
                "❌ پیام مورد نظر پیدا نشد!",
                reply_to_message_id=message_id
            )
            return True
    except Exception:
        bot.sendMessage(
            chat_id,
            "❌ خطا در دریافت پیام ریپلای شده!",
            reply_to_message_id=message_id
        )
        return True

    target_id = replied_message.get('sender_id')
    if not target_id:
        bot.sendMessage(
            chat_id,
            "❌ شناسه کاربر هدف پیدا نشد!",
            reply_to_message_id=message_id
        )
        return True

    user_data = db.get_key(target_id, {})
    if not user_data:
        bot.sendMessage(
            chat_id,
            "❌ کاربر در دیتابیس ثبت نام نشده است! لطفاً ربات را در پیوی استارت کنید.",
            reply_to_message_id=message_id
        )
        return True

    if len(text_parts) < 2:
        bot.sendMessage(
            chat_id,
            "❌ مقدار پوینت را وارد کن!\n"
            "مثال: rpoint 50",
            reply_to_message_id=message_id
        )
        return True

    try:
        point_amount = int(text_parts[1])
    except ValueError:
        bot.sendMessage(
            chat_id,
            "❌ مقدار وارد شده معتبر نیست! لطفاً یک عدد وارد کن.",
            reply_to_message_id=message_id
        )
        return True

    if point_amount <= 0:
        bot.sendMessage(
            chat_id,
            "❌ مقدار کاهش باید بزرگتر از صفر باشد!",
            reply_to_message_id=message_id
        )
        return True

    current_points = user_data.get('meow_points', 0)
    new_points = current_points - point_amount

    # پوینت نباید منفی شود
    if new_points < 0:
        new_points = 0
        bot.sendMessage(
            chat_id,
            f"⚠️ پوینت کاربر نمی‌تواند منفی شود، پوینت روی ۰ تنظیم شد.",
            reply_to_message_id=message_id
        )

    user_data['meow_points'] = new_points
    db.set_key(target_id, user_data)

    target_name = get_user_display_name(bot, target_id)
    actual_decrease = current_points - new_points

    bot.sendMessage(
        chat_id,
        f"✅ پوینت کاربر با موفقیت کاهش یافت!\n\n"
        f"👤 کاربر: {target_name}\n"
        f"🪪 آیدی: {target_id[:12]}...\n"
        f"💰 پوینت قبلی: {current_points:,}\n"
        f"💰 پوینت جدید: {new_points:,}\n"
        f"➖ کاهش: {actual_decrease:,}",
        reply_to_message_id=message_id
    )

    # ارسال پیام به خود کاربر (در صورت وجود chat_id)
    target_chat_id = user_data.get('chat_id')
    if target_chat_id:
        try:
            bot.sendMessage(
                target_chat_id,
                f"⚠️ ادمین پوینت شما را کاهش داد!\n"
                f"💰 پوینت جدید: {new_points:,}\n"
                f"➖ کاهش: {actual_decrease:,}"
            )
        except Exception:
            pass

    return True

# اضافه کردن به همان فایل (بعد از توابع پوینت)

def give_xp(text, message, sender_id, message_id, chat_id, bot):
    """
    هندلر افزایش XP کاربر (فقط برای ادمین)
    دستور: gxp [تعداد] (روی پیام کاربر ریپلای کنید)
    مثال: gxp 50  -> ۵۰ XP به کاربر اضافه می‌کند
    """
    text_parts = text.split()
    if not text_parts[0].lower() == "gxp":
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    reply_to_message_id = message.get('reply_to_message_id', None)
    if not reply_to_message_id:
        bot.sendMessage(
            chat_id,
            "❌ برای افزایش XP باید روی پیام کاربر ریپلای کنی!\n"
            "مثال: gxp 50 (روی پیام کاربر ریپلای کن)",
            reply_to_message_id=message_id
        )
        return True

    try:
        replied_message = bot.getMessage(chat_id + reply_to_message_id)
        if not replied_message:
            bot.sendMessage(
                chat_id,
                "❌ پیام مورد نظر پیدا نشد!",
                reply_to_message_id=message_id
            )
            return True
    except Exception:
        bot.sendMessage(
            chat_id,
            "❌ خطا در دریافت پیام ریپلای شده!",
            reply_to_message_id=message_id
        )
        return True

    target_id = replied_message.get('sender_id')
    if not target_id:
        bot.sendMessage(
            chat_id,
            "❌ شناسه کاربر هدف پیدا نشد!",
            reply_to_message_id=message_id
        )
        return True

    user_data = db.get_key(target_id, {})
    if not user_data:
        bot.sendMessage(
            chat_id,
            "❌ کاربر در دیتابیس ثبت نام نشده است! لطفاً ربات را در پیوی استارت کنید.",
            reply_to_message_id=message_id
        )
        return True

    if len(text_parts) < 2:
        bot.sendMessage(
            chat_id,
            "❌ مقدار XP را وارد کن!\n"
            "مثال: gxp 50",
            reply_to_message_id=message_id
        )
        return True

    try:
        xp_amount = int(text_parts[1])
    except ValueError:
        bot.sendMessage(
            chat_id,
            "❌ مقدار وارد شده معتبر نیست! لطفاً یک عدد وارد کن.",
            reply_to_message_id=message_id
        )
        return True

    if xp_amount <= 0:
        bot.sendMessage(
            chat_id,
            "❌ مقدار XP باید بزرگتر از صفر باشد!",
            reply_to_message_id=message_id
        )
        return True

    current_xp = user_data.get('meow_xp', 0)
    new_xp = current_xp + xp_amount
    user_data['meow_xp'] = new_xp
    db.set_key(target_id, user_data)

    target_name = get_user_display_name(bot, target_id)

    bot.sendMessage(
        chat_id,
        f"✅ XP کاربر با موفقیت افزایش یافت!\n\n"
        f"👤 کاربر: {target_name}\n"
        f"🪪 آیدی: {target_id[:12]}...\n"
        f"📈 XP قبلی: {current_xp:,}\n"
        f"📈 XP جدید: {new_xp:,}\n"
        f"➕ افزایش: +{xp_amount:,}",
        reply_to_message_id=message_id
    )

    # ارسال پیام به خود کاربر (در صورت وجود chat_id)
    target_chat_id = user_data.get('chat_id')
    if target_chat_id:
        try:
            bot.sendMessage(
                target_chat_id,
                f"🎉 ادمین XP شما را افزایش داد!\n"
                f"📈 XP جدید: {new_xp:,}\n"
                f"➕ افزایش: +{xp_amount:,}"
            )
        except Exception:
            pass

    return True


def remove_xp(text, message, sender_id, message_id, chat_id, bot):
    """
    هندلر کاهش XP کاربر (فقط برای ادمین)
    دستور: rxp [تعداد] (روی پیام کاربر ریپلای کنید)
    مثال: rxp 30  -> ۳۰ XP از کاربر کم می‌کند
    """
    text_parts = text.split()
    if not text_parts[0].lower() == "rxp":
        return False

    if not check_user_registered(sender_id, chat_id, bot):
        return True

    reply_to_message_id = message.get('reply_to_message_id', None)
    if not reply_to_message_id:
        bot.sendMessage(
            chat_id,
            "❌ برای کاهش XP باید روی پیام کاربر ریپلای کنی!\n"
            "مثال: rxp 30 (روی پیام کاربر ریپلای کن)",
            reply_to_message_id=message_id
        )
        return True

    try:
        replied_message = bot.getMessage(chat_id + reply_to_message_id)
        if not replied_message:
            bot.sendMessage(
                chat_id,
                "❌ پیام مورد نظر پیدا نشد!",
                reply_to_message_id=message_id
            )
            return True
    except Exception:
        bot.sendMessage(
            chat_id,
            "❌ خطا در دریافت پیام ریپلای شده!",
            reply_to_message_id=message_id
        )
        return True

    target_id = replied_message.get('sender_id')
    if not target_id:
        bot.sendMessage(
            chat_id,
            "❌ شناسه کاربر هدف پیدا نشد!",
            reply_to_message_id=message_id
        )
        return True

    user_data = db.get_key(target_id, {})
    if not user_data:
        bot.sendMessage(
            chat_id,
            "❌ کاربر در دیتابیس ثبت نام نشده است! لطفاً ربات را در پیوی استارت کنید.",
            reply_to_message_id=message_id
        )
        return True

    if len(text_parts) < 2:
        bot.sendMessage(
            chat_id,
            "❌ مقدار XP را وارد کن!\n"
            "مثال: rxp 30",
            reply_to_message_id=message_id
        )
        return True

    try:
        xp_amount = int(text_parts[1])
    except ValueError:
        bot.sendMessage(
            chat_id,
            "❌ مقدار وارد شده معتبر نیست! لطفاً یک عدد وارد کن.",
            reply_to_message_id=message_id
        )
        return True

    if xp_amount <= 0:
        bot.sendMessage(
            chat_id,
            "❌ مقدار کاهش باید بزرگتر از صفر باشد!",
            reply_to_message_id=message_id
        )
        return True

    current_xp = user_data.get('meow_xp', 0)
    new_xp = current_xp - xp_amount

    if new_xp < 0:
        new_xp = 0
        bot.sendMessage(
            chat_id,
            f"⚠️ XP کاربر نمی‌تواند منفی شود، XP روی ۰ تنظیم شد.",
            reply_to_message_id=message_id
        )

    user_data['meow_xp'] = new_xp
    db.set_key(target_id, user_data)

    target_name = get_user_display_name(bot, target_id)
    actual_decrease = current_xp - new_xp

    bot.sendMessage(
        chat_id,
        f"✅ XP کاربر با موفقیت کاهش یافت!\n\n"
        f"👤 کاربر: {target_name}\n"
        f"🪪 آیدی: {target_id[:12]}...\n"
        f"📈 XP قبلی: {current_xp:,}\n"
        f"📈 XP جدید: {new_xp:,}\n"
        f"➖ کاهش: {actual_decrease:,}",
        reply_to_message_id=message_id
    )

    # ارسال پیام به خود کاربر (در صورت وجود chat_id)
    target_chat_id = user_data.get('chat_id')
    if target_chat_id:
        try:
            bot.sendMessage(
                target_chat_id,
                f"⚠️ ادمین XP شما را کاهش داد!\n"
                f"📈 XP جدید: {new_xp:,}\n"
                f"➖ کاهش: {actual_decrease:,}"
            )
        except Exception:
            pass

    return True 

def give_meow(text, message, sender_id, message_id, chat_id, bot):
    """
    هندلر افزایش تعداد میو کاربر (فقط برای ادمین)
    دستور: gmeow [تعداد] (روی پیام کاربر ریپلای کنید)
    مثال: gmeow 5  -> ۵ تا به تعداد میوهای کاربر اضافه می‌کند
    """
    text_parts = text.split()
    if not text_parts[0].lower() == "gmeow":
        return False



    if not check_user_registered(sender_id, chat_id, bot):
        return True

    reply_to_message_id = message.get('reply_to_message_id', None)
    if not reply_to_message_id:
        bot.sendMessage(
            chat_id,
            "❌ برای افزایش میو باید روی پیام کاربر ریپلای کنی!\n"
            "مثال: gmeow 5 (روی پیام کاربر ریپلای کن)",
            reply_to_message_id=message_id
        )
        return True

    try:
        replied_message = bot.getMessage(chat_id + reply_to_message_id)
        if not replied_message:
            bot.sendMessage(
                chat_id,
                "❌ پیام مورد نظر پیدا نشد!",
                reply_to_message_id=message_id
            )
            return True
    except Exception:
        bot.sendMessage(
            chat_id,
            "❌ خطا در دریافت پیام ریپلای شده!",
            reply_to_message_id=message_id
        )
        return True

    target_id = replied_message.get('sender_id')
    if not target_id:
        bot.sendMessage(
            chat_id,
            "❌ شناسه کاربر هدف پیدا نشد!",
            reply_to_message_id=message_id
        )
        return True

    user_data = db.get_key(target_id, {})
    if not user_data:
        bot.sendMessage(
            chat_id,
            "❌ کاربر در دیتابیس ثبت نام نشده است! لطفاً ربات را در پیوی استارت کنید.",
            reply_to_message_id=message_id
        )
        return True

    if len(text_parts) < 2:
        bot.sendMessage(
            chat_id,
            "❌ مقدار میو را وارد کن!\n"
            "مثال: gmeow 5",
            reply_to_message_id=message_id
        )
        return True

    try:
        meow_amount = int(text_parts[1])
    except ValueError:
        bot.sendMessage(
            chat_id,
            "❌ مقدار وارد شده معتبر نیست! لطفاً یک عدد وارد کن.",
            reply_to_message_id=message_id
        )
        return True

    if meow_amount <= 0:
        bot.sendMessage(
            chat_id,
            "❌ مقدار میو باید بزرگتر از صفر باشد!",
            reply_to_message_id=message_id
        )
        return True

    current_meows = user_data.get('meow_count', 0)
    new_meows = current_meows + meow_amount
    user_data['meow_count'] = new_meows
    db.set_key(target_id, user_data)

    target_name = get_user_display_name(bot, target_id)

    bot.sendMessage(
        chat_id,
        f"✅ تعداد میوهای کاربر با موفقیت افزایش یافت!\n\n"
        f"👤 کاربر: {target_name}\n"
        f"🪪 آیدی: {target_id[:12]}...\n"
        f"🐾 میو قبلی: {current_meows:,}\n"
        f"🐾 میو جدید: {new_meows:,}\n"
        f"➕ افزایش: +{meow_amount:,}",
        reply_to_message_id=message_id
    )

    # ارسال پیام به خود کاربر (در صورت وجود chat_id)
    target_chat_id = user_data.get('chat_id')
    if target_chat_id:
        try:
            bot.sendMessage(
                target_chat_id,
                f"🎉 ادمین تعداد میوهای شما را افزایش داد!\n"
                f"🐾 میو جدید: {new_meows:,}\n"
                f"➕ افزایش: +{meow_amount:,}"
            )
        except Exception:
            pass

    return True


def remove_meow(text, message, sender_id, message_id, chat_id, bot):
    """
    هندلر کاهش تعداد میو کاربر (فقط برای ادمین)
    دستور: rmeow [تعداد] (روی پیام کاربر ریپلای کنید)
    مثال: rmeow 3  -> ۳ تا از تعداد میوهای کاربر کم می‌کند
    """
    text_parts = text.split()
    if not text_parts[0].lower() == "rmeow":
        return False


    if not check_user_registered(sender_id, chat_id, bot):
        return True

    reply_to_message_id = message.get('reply_to_message_id', None)
    if not reply_to_message_id:
        bot.sendMessage(
            chat_id,
            "❌ برای کاهش میو باید روی پیام کاربر ریپلای کنی!\n"
            "مثال: rmeow 3 (روی پیام کاربر ریپلای کن)",
            reply_to_message_id=message_id
        )
        return True

    try:
        replied_message = bot.getMessage(chat_id + reply_to_message_id)
        if not replied_message:
            bot.sendMessage(
                chat_id,
                "❌ پیام مورد نظر پیدا نشد!",
                reply_to_message_id=message_id
            )
            return True
    except Exception:
        bot.sendMessage(
            chat_id,
            "❌ خطا در دریافت پیام ریپلای شده!",
            reply_to_message_id=message_id
        )
        return True

    target_id = replied_message.get('sender_id')
    if not target_id:
        bot.sendMessage(
            chat_id,
            "❌ شناسه کاربر هدف پیدا نشد!",
            reply_to_message_id=message_id
        )
        return True

    user_data = db.get_key(target_id, {})
    if not user_data:
        bot.sendMessage(
            chat_id,
            "❌ کاربر در دیتابیس ثبت نام نشده است! لطفاً ربات را در پیوی استارت کنید.",
            reply_to_message_id=message_id
        )
        return True

    if len(text_parts) < 2:
        bot.sendMessage(
            chat_id,
            "❌ مقدار میو را وارد کن!\n"
            "مثال: rmeow 3",
            reply_to_message_id=message_id
        )
        return True

    try:
        meow_amount = int(text_parts[1])
    except ValueError:
        bot.sendMessage(
            chat_id,
            "❌ مقدار وارد شده معتبر نیست! لطفاً یک عدد وارد کن.",
            reply_to_message_id=message_id
        )
        return True

    if meow_amount <= 0:
        bot.sendMessage(
            chat_id,
            "❌ مقدار کاهش باید بزرگتر از صفر باشد!",
            reply_to_message_id=message_id
        )
        return True

    current_meows = user_data.get('meow_count', 0)
    new_meows = current_meows - meow_amount

    if new_meows < 0:
        new_meows = 0
        bot.sendMessage(
            chat_id,
            f"⚠️ تعداد میوهای کاربر نمی‌تواند منفی شود، روی ۰ تنظیم شد.",
            reply_to_message_id=message_id
        )

    user_data['meow_count'] = new_meows
    db.set_key(target_id, user_data)

    target_name = get_user_display_name(bot, target_id)
    actual_decrease = current_meows - new_meows

    bot.sendMessage(
        chat_id,
        f"✅ تعداد میوهای کاربر با موفقیت کاهش یافت!\n\n"
        f"👤 کاربر: {target_name}\n"
        f"🪪 آیدی: {target_id[:12]}...\n"
        f"🐾 میو قبلی: {current_meows:,}\n"
        f"🐾 میو جدید: {new_meows:,}\n"
        f"➖ کاهش: {actual_decrease:,}",
        reply_to_message_id=message_id
    )

    target_chat_id = user_data.get('chat_id')
    if target_chat_id:
        try:
            bot.sendMessage(
                target_chat_id,
                f"⚠️ ادمین تعداد میوهای شما را کاهش داد!\n"
                f"🐾 میو جدید: {new_meows:,}\n"
                f"➖ کاهش: {actual_decrease:,}"
            )
        except Exception:
            pass

    return True