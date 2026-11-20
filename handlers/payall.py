from config import ADMIN_ID
from core.db_instance import db

def handle_payall(text, message, sender_id, message_id, chat_id, bot):
    if not text.lower().startswith("payall"):
        return False
    
    if sender_id != ADMIN_ID[0]:
        bot.sendMessage(
            chat_id,
            "🚫 شما دسترسی به این کامند ندارید!",
            reply_to_message_id=message_id
        )
        return True
    
    all_users = db.get_all_keys()
    text_parts = text.split()
    
    if len(text_parts) < 2:
        bot.sendMessage(
            chat_id,
            "❌ مقدار پوینت را وارد کن!\n"
            "مثال: payall 100\n"
            "یا: payall 100 5 (فقط به کاربران با سطح ۵ و بالاتر)",
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

    # بررسی پارامتر سطح (اختیاری)
    level_threshold = None
    if len(text_parts) >= 3:
        try:
            level_threshold = int(text_parts[2])
            if level_threshold < 1:
                bot.sendMessage(
                    chat_id,
                    "❌ سطح باید حداقل ۱ باشد!",
                    reply_to_message_id=message_id
                )
                return True
        except ValueError:
            bot.sendMessage(
                chat_id,
                "❌ مقدار سطح وارد شده معتبر نیست! لطفاً یک عدد وارد کن.",
                reply_to_message_id=message_id
            )
            return True

    count_paid = 0
    total_points_given = 0
    skipped_low_level = 0
    skipped_no_points = 0

    for uid in all_users:
        if not uid:
            continue
        if uid.startswith('u') or uid.startswith('b'):
            user_data = db.get_key(uid, {})
            if isinstance(user_data, dict) and user_data:
                # بررسی سطح اگر شرط تعیین شده باشد
                if level_threshold is not None:
                    user_level = user_data.get('meow_level', 1)
                    if user_level < level_threshold:
                        skipped_low_level += 1
                        continue
                value = user_data.get('meow_points', 0)
                if value <= 0:
                    skipped_no_points += 1
                    continue

                user_data['meow_points'] = value + point_amount
                db.set_key(uid, user_data)
                count_paid += 1
                total_points_given += point_amount

    # ارسال گزارش نهایی
    if count_paid == 0:
        msg = "❌ هیچ کاربری برای دریافت پوینت یافت نشد!"
        if skipped_low_level > 0:
            msg += f"\n📊 تعداد کاربران با سطح کمتر از {level_threshold}: {skipped_low_level}"
        if skipped_no_points > 0:
            msg += f"\n📊 تعداد کاربران با پوینت صفر یا منفی: {skipped_no_points}"
        bot.sendMessage(chat_id, msg, reply_to_message_id=message_id)
    else:
        msg = f"✅ عملیات payall با موفقیت انجام شد!\n\n"
        msg += f"💰 مبلغ پرداختی به هر کاربر: {point_amount:,} پوینت\n"
        msg += f"👥 تعداد کاربران دریافت‌کننده: {count_paid:,}\n"
        msg += f"💳 کل پوینت‌های توزیع‌شده: {total_points_given:,} پوینت\n"
        msg += f"📊 میانگین پوینت دریافتی هر کاربر: {point_amount:,} پوینت"
        
        if level_threshold is not None:
            msg += f"\n🎯 شرط سطح: کاربران با سطح >= {level_threshold}"
            if skipped_low_level > 0:
                msg += f"\n📊 کاربران با سطح کمتر از {level_threshold} (رد شده): {skipped_low_level}"
        if skipped_no_points > 0:
            msg += f"\n📊 کاربران با پوینت صفر/منفی (رد شده): {skipped_no_points}"

        bot.sendMessage(chat_id, msg, reply_to_message_id=message_id)
    
    return True