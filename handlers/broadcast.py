import time
from config import ADMIN_ID
from core.db_instance import db
from libs.BackgroundTask import BackgroundTask


def handle_broadcast_groups(message:dict,text: str, sender_id: str, bot, chat_id: str, message_id: str):
    bgtask = BackgroundTask(
        _handle_broadcast_groups,
        (message,text, sender_id, bot, chat_id, message_id)
    )
    bgtask.start()

def _handle_broadcast_groups(message:dict,text: str, sender_id: str, bot, chat_id: str, message_id: str) -> bool:
    """
    هندلر ارسال پیام همگانی به گروه‌ها (فقط ادمین)
    دستور: bcg [متن]  یا  پیام همگانی گروه [متن]
    
    Args:
        text: متن کامل پیام
        sender_id: شناسه فرستنده
        bot: نمونه از API
        chat_id: شناسه چت جاری (برای گزارش)
        message_id: شناسه پیام جاری

    Returns:
        bool: True اگر هندلر پردازش کرده، False اگر مربوط نبود
    """
    # تشخیص دستور - تغییر به bcg
    if not text.lower().startswith("bcg"):
        return False

    # بررسی دسترسی ادمین
    if sender_id != ADMIN_ID[0]:
        return True

    # استخراج متن پیام
    text_parts = text.split(maxsplit=1)
    if len(text_parts) < 2:
        bot.sendMessage(
            chat_id,
            "❌ لطفاً متن پیام را وارد کنید!\n"
            "مثال: bcg سلام به همه گروه‌ها!",
            reply_to_message_id=message_id
        )
        return True

    metadata = message.get('metadata',None)

    broadcast_text = text_parts[1].strip()

    if broadcast_text.startswith('"') and broadcast_text.endswith('"'):
        broadcast_text = broadcast_text[1:-1]
    elif broadcast_text.startswith("'") and broadcast_text.endswith("'"):
        broadcast_text = broadcast_text[1:-1]

    if not broadcast_text:
        bot.sendMessage(
            chat_id,
            "❌ متن پیام نمی‌تواند خالی باشد!",
            reply_to_message_id=message_id
        )
        return True

    # پیام شروع
    bot.sendMessage(
        chat_id,
        f"📤 در حال ارسال پیام همگانی به گروه‌ها...\n"
        f"📝 متن: {broadcast_text[:100]}{'...' if len(broadcast_text) > 100 else ''}",
        reply_to_message_id=message_id
    )

    groups_chat_ids = getattr(bot, 'groups', [])
    if not groups_chat_ids:
        bot.sendMessage(
            chat_id,
            "⚠️ هیچ گروهی برای ارسال یافت نشد!",
            reply_to_message_id=message_id
        )
        return True

    success_count = 0
    fail_count = 0

    for group_chat_id in groups_chat_ids:
        try:
            bot.sendMessage(
                group_chat_id,
                broadcast_text,
                metadata=metadata
            )
            success_count += 1
            time.sleep(10)  # تاخیر برای جلوگیری از محدودیت
        except Exception as e:
            fail_count += 1
            print(f"خطا در ارسال به گروه {group_chat_id}: {e}")

    # گزارش نهایی
    result_message = (
        f"📊 گزارش ارسال پیام همگانی به گروه‌ها:\n\n"
        f"✅ ارسال موفق: {success_count} گروه\n"
        f"❌ ارسال ناموفق: {fail_count} گروه\n"
        f"👥 کل گروه‌ها: {len(groups_chat_ids)}\n\n"
        f"📝 متن پیام:\n{broadcast_text[:200]}{'...' if len(broadcast_text) > 200 else ''}\n\n"
        f"─────────────────\n"
        f"📅 زمان ارسال: {time.strftime('%Y/%m/%d %H:%M:%S')}"
    )
    bot.sendMessage(chat_id, result_message, reply_to_message_id=message_id)

    broadcast_history = db.get_key("broadcast_history", [])
    broadcast_history.append({
        'admin_id': sender_id,
        'text': broadcast_text,
        'type': 'groups',
        'success_count': success_count,
        'fail_count': fail_count,
        'total_groups': len(groups_chat_ids),
        'time': time.time()
    })
    if len(broadcast_history) > 50:
        broadcast_history = broadcast_history[-50:]
    db.set_key("broadcast_history", broadcast_history)

    return True

def handle_broadcast(message,text: str, sender_id: str, bot, chat_id: str, message_id: str):
    bgtask = BackgroundTask(
            _handle_broadcast,
            (message,text, sender_id, bot, chat_id, message_id)
        )
    bgtask.start()

def _handle_broadcast(message,text: str, sender_id: str, bot, chat_id: str, message_id: str) -> bool:
    """
    هندلر پیام همگانی (فقط ادمین)
    برگرداندن True یعنی هندلر پردازش کرده، False یعنی هندلر مربوطه نیست
    """

    # اطمینان از اینکه ADMIN_ID یک لیست است (اگر رشته است، تبدیل به لیست)
    admin_list = [ADMIN_ID[0]]

    # ---- پیام همگانی ----
    if text.lower().startswith("broadcast") or text.lower().startswith("پیام همگانی"):
        if sender_id not in admin_list:
            bot.sendMessage(
                chat_id,
                "🚫 شما دسترسی به این کامند ندارید! این کامند فقط برای ادمین است.",
                reply_to_message_id=message_id
            )
            return True  # هندلر پردازش شد (اجازه نداشت)

        # استخراج متن پیام
        text_parts = text.split(maxsplit=1)
        if len(text_parts) < 2:
            bot.sendMessage(
                chat_id,
                "❌ لطفاً متن پیام را وارد کنید!\n"
                "مثال: broadcast سلام به همه کاربران!",
                reply_to_message_id=message_id
            )
            return True

        broadcast_text = text_parts[1].strip()

        # حذف نقل قول‌های اضافی
        if broadcast_text.startswith('"') and broadcast_text.endswith('"'):
            broadcast_text = broadcast_text[1:-1]
        elif broadcast_text.startswith("'") and broadcast_text.endswith("'"):
            broadcast_text = broadcast_text[1:-1]

        if not broadcast_text:
            bot.sendMessage(
                chat_id,
                "❌ متن پیام نمی‌تواند خالی باشد!",
                reply_to_message_id=message_id
            )
            return True
        metadata = message.get('metadata',None)

        # پیام شروع
        bot.sendMessage(
            chat_id,
            f"📤 در حال ارسال پیام همگانی...\n"
            f"📝 متن: {broadcast_text[:100]}{'...' if len(broadcast_text) > 100 else ''}",
            reply_to_message_id=message_id
        )

        # دریافت کاربران
        all_users = db.get_all_keys()
        target_users = []
        for uid in all_users:
            if not uid:
                continue
            if uid.startswith('u') or uid.startswith('b'):
                user_data = db.get_key(uid, {})
                if isinstance(user_data, dict) and user_data:
                    chat_id_user = user_data.get('chat_id')
                    if chat_id_user:
                        target_users.append((uid, chat_id_user))

        total_users = len(target_users)

        success_count = 0
        fail_count = 0

        for uid, user_chat_id in target_users:
            try:
                bot.sendMessage(
                    user_chat_id,
                    broadcast_text,
                    metadata=metadata
                )
                success_count += 1
                time.sleep(10)  # تاخیر برای جلوگیری از محدودیت
            except Exception as e:
                fail_count += 1
                print(f"خطا در ارسال به {uid}: {e}")

        # گزارش نهایی
        result_message = (
            f"📊 گزارش ارسال پیام همگانی:\n\n"
            f"✅ ارسال موفق: {success_count} کاربر\n"
            f"❌ ارسال ناموفق: {fail_count} کاربر\n"
            f"👥 کل کاربران: {total_users}\n\n"
            f"📝 متن پیام:\n{broadcast_text[:200]}{'...' if len(broadcast_text) > 200 else ''}\n\n"
            f"─────────────────\n"
            f"📅 زمان ارسال: {time.strftime('%Y/%m/%d %H:%M:%S')}"
        )
        bot.sendMessage(chat_id, result_message, reply_to_message_id=message_id)

        # ثبت تاریخچه
        broadcast_history = db.get_key("broadcast_history", [])
        broadcast_history.append({
            'admin_id': sender_id,
            'text': broadcast_text,
            'success_count': success_count,
            'fail_count': fail_count,
            'total_users': total_users,
            'time': time.time()
        })
        if len(broadcast_history) > 50:
            broadcast_history = broadcast_history[-50:]
        db.set_key("broadcast_history", broadcast_history)

        return True

    # ---- تاریخچه ارسال ----
    if text.lower() in ["broadcast history", "تاریخچه ارسال", "پیام همگانی تاریخچه"]:
        if sender_id not in admin_list:
            bot.sendMessage(
                chat_id,
                "🚫 شما دسترسی به این کامند ندارید!",
                reply_to_message_id=message_id
            )
            return True

        broadcast_history = db.get_key("broadcast_history", [])
        if not broadcast_history:
            bot.sendMessage(
                chat_id,
                "📭 هنوز هیچ پیام همگانی ارسال نشده است.",
                reply_to_message_id=message_id
            )
            return True

        history_message = "📜 تاریخچه پیام‌های همگانی (۱۰ مورد آخر):\n\n"
        for idx, item in enumerate(reversed(broadcast_history[-10:]), 1):
            send_time = time.strftime('%Y/%m/%d %H:%M', time.localtime(item.get('time', 0)))
            text_preview = item.get('text', '')[:50]
            if len(item.get('text', '')) > 50:
                text_preview += '...'
            history_message += (
                f"{idx}. 📅 {send_time}\n"
                f"   📝 {text_preview}\n"
                f"   ✅ {item.get('success_count', 0)} موفق | ❌ {item.get('fail_count', 0)} ناموفق\n\n"
            )
        bot.sendMessage(chat_id, history_message, reply_to_message_id=message_id)
        return True

# ---- آمار کاربران ----
    if text.lower() in ["user stats", "آمار کاربران", "کاربران"]:
        if sender_id not in admin_list:
            bot.sendMessage(
                chat_id,
                "🚫 شما دسترسی به این کامند ندارید!",
                reply_to_message_id=message_id
            )
            return True

        all_users = db.get_all_keys()
        total_users = 0
        registered_users = 0
        total_points = 0
        total_meows = 0
        total_bank_accounts = 0
        total_bank_balance = 0

        for uid in all_users:
            if not uid:
                continue
            if uid.startswith('u') or uid.startswith('b'):
                total_users += 1
                data = db.get_key(uid, {})
                if isinstance(data, dict) and data:
                    if data.get('chat_id'):
                        registered_users += 1
                    total_points += data.get('meow_points', 0)
                    total_meows += data.get('meow_count', 0)
                    
                    # آمار بانک
                    bank = data.get('bank')
                    if isinstance(bank, dict) and bank.get('account_number'):
                        total_bank_accounts += 1
                        total_bank_balance += bank.get('balance', 0)

        avg_points = total_points // total_users if total_users > 0 else 0
        avg_meows = total_meows // total_users if total_users > 0 else 0
        avg_bank_balance = total_bank_balance // total_bank_accounts if total_bank_accounts > 0 else 0
        total_points += total_bank_balance
        bot.sendMessage(
            chat_id,
            f"📊 آمار کاربران ربات:\n\n"
            f"👥 کل کاربران: {total_users:,}\n"
            f"✅ کاربران ثبت‌نام شده: {registered_users:,}\n"
            f"💰 کل پوینت‌ها: {total_points:,}\n"
            f"🐾 کل میوها: {total_meows:,}\n"
            f"📈 میانگین پوینت: {avg_points:,}\n"
            f"📊 میانگین میو: {avg_meows:,}\n\n"
            f"🏦 آمار بانک:\n"
            f"┘─ تعداد حساب‌های باز: {total_bank_accounts:,}\n"
            f"┘─ کل موجودی بانک: {total_bank_balance:,} پوینت\n"
            f"┘─ میانگین موجودی هر حساب: {avg_bank_balance:,} پوینت",
            reply_to_message_id=message_id
        )
        return True
    
    # ---- پاک کردن تاریخچه ----
    if text.lower() in ["clear broadcast", "پاک کردن تاریخچه"]:
        if sender_id not in admin_list:
            bot.sendMessage(
                chat_id,
                "🚫 شما دسترسی به این کامند ندارید!",
                reply_to_message_id=message_id
            )
            return True

        db.set_key("broadcast_history", [])
        bot.sendMessage(
            chat_id,
            "🗑️ تاریخچه پیام‌های همگانی پاک شد.",
            reply_to_message_id=message_id
        )
        return True

    # اگر هیچ کدام از دستورات نبود، False برگردان
    return False