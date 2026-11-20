# handlers/help.py
"""هندلر دستور راهنما"""

from config import HELP_MESSAGE
from core.helpers import cur

HELP_KEYWORDS = ["help", "کامندها", "راهنما", "/help"]


def handle_help(text, chat_type, sender_id, message_id, chat_id, bot) -> bool:
    if text.lower() not in HELP_KEYWORDS:
        return False

    if not cur(chat_type, sender_id, message_id, chat_id, bot):
        return True

    bot.sendMessage(chat_id, """
🐱 وارد کانال زیر شوید و پیام سنجاق شده/پین شده را بخوانید. 🐱
کانال: @MeowNekoChannel
""", reply_to_message_id=message_id)
    return True
