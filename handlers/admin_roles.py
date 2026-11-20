# handlers/admin_roles.py
"""هندلرهای مدیریت نقش‌ها (فقط ادمین)"""

from config import ADMIN_ID
from core.db_instance import db
from core.helpers import get_user_display_name
from core.roles import VALID_ROLES, set_user_role, get_user_role, get_role_display_name


def handle_set_role(text, message, sender_id, message_id, chat_id, bot) -> bool:
    """
    دستور: setrole [نقش] (روی پیام کاربر ریپلای کن)
    نقش‌های معتبر: member, helper, special, premium
    مثال: setrole helper
    """
    if not text.lower().startswith("setrole "):
        return False

    # بررسی ادمین
    if sender_id not in ADMIN_ID:
        bot.sendMessage(chat_id, "🚫 شما دسترسی به این کامند ندارید!", reply_to_message_id=message_id)
        return True

    # استخراج نقش
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        bot.sendMessage(chat_id, "❌ لطفاً نقش مورد نظر را وارد کن!\nمثال: setrole helper", reply_to_message_id=message_id)
        return True

    role = parts[1].strip().lower()
    if role not in VALID_ROLES:
        bot.sendMessage(chat_id, f"❌ نقش '{role}' معتبر نیست!\nنقش‌های مجاز: {', '.join(VALID_ROLES)}", reply_to_message_id=message_id)
        return True

    # بررسی ریپلای
    reply_to = message.get('reply_to_message_id')
    if not reply_to:
        bot.sendMessage(chat_id, "❌ روی پیام کاربر ریپلای کن!", reply_to_message_id=message_id)
        return True

    try:
        replied = bot.getMessage(chat_id + reply_to)
        if not replied:
            bot.sendMessage(chat_id, "❌ پیام پیدا نشد!", reply_to_message_id=message_id)
            return True
    except:
        bot.sendMessage(chat_id, "❌ خطا در دریافت پیام!", reply_to_message_id=message_id)
        return True

    target_id = replied.get('sender_id')
    if not target_id:
        bot.sendMessage(chat_id, "❌ شناسه کاربر پیدا نشد!", reply_to_message_id=message_id)
        return True

    # تنظیم نقش
    if set_user_role(target_id, role):
        target_name = get_user_display_name(bot, target_id)
        role_display = get_role_display_name(role)
        bot.sendMessage(
            chat_id,
            f"✅ نقش کاربر با موفقیت تغییر کرد!\n\n"
            f"👤 کاربر: {target_name}\n"
            f"🎖️ نقش جدید: {role_display}",
            reply_to_message_id=message_id
        )
        # اطلاع‌رسانی به خود کاربر
        target_data = db.get_key(target_id, {})
        target_chat_id = target_data.get('chat_id')
        if target_chat_id:
            try:
                bot.sendMessage(
                    target_chat_id,
                    f"🔄 نقش شما توسط ادمین تغییر کرد!\n"
                    f"🎖️ نقش جدید: {role_display}"
                )
            except:
                pass
    else:
        bot.sendMessage(chat_id, "❌ خطا در تغییر نقش!", reply_to_message_id=message_id)

    return True


def handle_remove_role(text, message, sender_id, message_id, chat_id, bot) -> bool:
    """
    دستور: removerole (روی پیام کاربر ریپلای کن) -> نقش را به member بازمی‌گرداند
    """
    if not text.lower().startswith("removerole"):
        return False

    if sender_id not in ADMIN_ID:
        bot.sendMessage(chat_id, "🚫 شما دسترسی به این کامند ندارید!", reply_to_message_id=message_id)
        return True

    reply_to = message.get('reply_to_message_id')
    if not reply_to:
        bot.sendMessage(chat_id, "❌ روی پیام کاربر ریپلای کن!", reply_to_message_id=message_id)
        return True

    try:
        replied = bot.getMessage(chat_id + reply_to)
        if not replied:
            bot.sendMessage(chat_id, "❌ پیام پیدا نشد!", reply_to_message_id=message_id)
            return True
    except:
        bot.sendMessage(chat_id, "❌ خطا در دریافت پیام!", reply_to_message_id=message_id)
        return True

    target_id = replied.get('sender_id')
    if not target_id:
        bot.sendMessage(chat_id, "❌ شناسه کاربر پیدا نشد!", reply_to_message_id=message_id)
        return True

    if set_user_role(target_id, "member"):
        target_name = get_user_display_name(bot, target_id)
        bot.sendMessage(
            chat_id,
            f"✅ نقش کاربر به عضو (member) بازگردانده شد.\n👤 کاربر: {target_name}",
            reply_to_message_id=message_id
        )
    else:
        bot.sendMessage(chat_id, "❌ خطا!", reply_to_message_id=message_id)

    return True


def handle_get_user_role(text, message, sender_id, message_id, chat_id, bot) -> bool:
    """
    دستور: myrole - نمایش نقش خود کاربر
    """
    if text.strip().lower() != "myrole":
        return False

    role = get_user_role(sender_id)
    role_display = get_role_display_name(role)
    bot.sendMessage(
        chat_id,
        f"🎖️ نقش شما: {role_display}",
        reply_to_message_id=message_id
    )
    return True

def get_message_data(text, message, sender_id, message_id, chat_id, bot):
    if text.strip().lower() != "get_data":
        return False
    reply_to_message_id = message.get('reply_to_message_id', None)
    
    msg_data = bot.getMessage(chat_id+reply_to_message_id)

    print(msg_data)