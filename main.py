# main.py
"""نقطه ورود اصلی ربات میویی - تمام هندلرها اینجا به ترتیب فراخوانی می‌شوند"""

from rubik import API, NewMessageHandler, EditedMessageHandler, get_chat_type

from config import BOT_TOKEN, USER_SPAM_LIMIT, SPAM_WINDOW, ADMIN_ID,DARAMET_USERNAME,DARAMET_TOKEN
from core.db_instance import db
from core.antispam import is_user_banned, check_spam, ban_user_for_spam
from core.antilink import handle_antilink
from core.donate_handler import start_daramet_listener

from handlers.start import handle_start, ensure_user_exists
from handlers.ban import handle_pay_fine, handle_ban_status
from handlers.meow import handle_meow
from handlers.profile import handle_profile, handle_profile_reply
from handlers.leaderboard import handle_top_points, handle_top_meows
from handlers.group import handle_join_group, handle_land_points_leaderboard, handle_land_meows_leaderboard
from handlers.transfer import handle_pay
from handlers.help import handle_help
from handlers.broadcast import handle_broadcast, handle_broadcast_groups
from handlers.payall import handle_payall
from handlers.gives_admin import give_level, remove_level, give_points, remove_points, give_xp, remove_xp,give_meow,remove_meow

from handlers.games.soccer import handle_soccer, handle_soccer_stats, handle_soccer_leaderboard
from handlers.games.dice import handle_dice
from handlers.games.basketball import handle_basketball
from handlers.games.volleyball import handle_volleyball
from handlers.games.fishing import (
    handle_fishing,
    handle_fishing_stats,
    handle_fishing_leaderboard,
    handle_fish_inventory,
    handle_sell_fish_start,
    handle_fishing_conversation,
)
from handlers.pet import (
    handle_pet,
    handle_pet_buy_conversation,
    handle_feed_pet,
    handle_collect_pet,
    handle_upgrade_pet,
    handle_rankup_pet,
    handle_rename_pet,
)
from handlers.fridge import (
    handle_fridge_view,
    handle_fridge_store_start,
    handle_fridge_cook_start,
    handle_fridge_sell_start,
    handle_fridge_feed_start,
    handle_fridge_upgrade,
    handle_fridge_conversation,
)
from handlers.street_cats import handle_rescue_attempt, handle_kindness_leaderboard
from handlers.bank import (
    handle_bank_entry,
    handle_bank_deposit,
    handle_bank_withdraw,
    handle_bank_change_number,
    handle_bank_transfer,
)
from handlers.factory import (
    handle_factory_entry,
    handle_hire_worker,
    handle_fire_worker,
    handle_start_production,
    handle_upgrade_warehouse,
    handle_upgrade_machine,
    handle_sell_start,
    handle_market_view,
    handle_factory_conversation,
)
from handlers.smuggling import handle_smuggling_entry, handle_start_smuggling
from handlers.street_market import (
    handle_market_entry,
    handle_buy_street_cat,
    handle_buy_worm,
    handle_use_worm,
)
from handlers.city_leaderboard import (
    handle_loud_city_leaderboard,
    handle_population_city_leaderboard,
    handle_treasury_city_leaderboard,
    handle_fish_market_city_leaderboard,
)
from handlers.shop import (
    handle_shop_entry,
    handle_shop_buy,
    handle_shop_buy_with_wallet,
    handle_wallet_charge,
    handle_wallet_balance,
    handle_shop_check,
)
from handlers.admin_roles import (
    handle_set_role,
    handle_remove_role,
    handle_get_user_role,
    get_message_data
)
from handlers.street_market import (
    handle_market_entry,
    handle_buy_street_cat,
    handle_buy_worm,
    handle_buy_level,
    handle_use_worm,
    handle_use_gift,
)
from handlers.admin_gift import (
    handle_create_gift,
    handle_list_gifts,
    handle_delete_gift,
)
from handlers.group import (
    handle_join_group,
    handle_leave_group,
    handle_group_stats,
    handle_land_points_leaderboard,
    handle_land_meows_leaderboard,
)
from handlers.helpdesk import (
    handle_helpme,
    handle_answer_command,
    handle_rate_ticket,
    handle_my_tickets,
    handle_helper_stats,
    handle_helper_leaderboard,
)
from handlers.invite import (
    handle_generate_invite,
    handle_use_invite,
    handle_my_invite,
    handle_invite_leaderboard,
)

def new_message(update: dict, bot: API):
    chat_id: str = update.get('chat_id')
    chat_type: str = get_chat_type(chat_id)
    
    message = update.get('new_message', {})
    if not int(message.get('time', 0)) > bot.time_run:
        return
    text = message.get('text', None)
    if not text:
        return

    message_id = message.get("message_id", None)
    sender_id = message.get('sender_id', None)
    if handle_antilink(sender_id,text, chat_type, chat_id, message_id, bot):
        return
    # ============ آنتی اسپم ============
    # اگر کاربر در زندان میویی است، فقط دستور پرداخت جریمه پردازش می‌شود
    if is_user_banned(sender_id):
        handle_pay_fine(text, sender_id, chat_id, message_id, bot)
        return
    
    if not check_spam(sender_id):
        ban_user_for_spam(sender_id)
        bot.sendMessage(
            chat_id,
            f"🚫 شما به دلیل ارسال بیش از {USER_SPAM_LIMIT} پیام در {SPAM_WINDOW} ثانیه به زندان میویی فرستاده شدید!\n"
            f"⏳ مدت محرومیت: 15 دقیقه\n"
            f"💰 برای پرداخت جریمه: `پرداخت جریمه`",
            reply_to_message_id=message_id
        )
        return
    
    # اگر در پیوی هستیم و دستور /start است
    if handle_start(text, chat_type, sender_id, chat_id, message_id, bot):
        return
    
    if handle_group_stats(text, chat_type, sender_id, message_id, chat_id, bot):
        return
        
    # اگر کاربر وجود نداشته باشد، رکورد اولیه او را ایجاد می‌کنیم
    ensure_user_exists(sender_id, chat_id, chat_type)

    # وضعیت زندان میویی
    if handle_ban_status(text, sender_id, chat_id, message_id, bot):
        return

    # اگر کاربر وسط یک کانورسیشن فعال است (مثل فروش ماهی یا خرید پیشی)، اول اون رو پردازش کن
    if handle_fishing_conversation(text, sender_id, message_id, chat_id, bot):
        return
    if handle_pet_buy_conversation(text, sender_id, message_id, chat_id, bot):
        return
    if handle_fridge_conversation(text, sender_id, message_id, chat_id, bot):
        return
    if handle_factory_conversation(text, sender_id, message_id, chat_id, bot):
        return

    # میو کردن (مکانیزم اصلی کسب پوینت)
    if handle_meow(text, chat_type, sender_id, message_id, chat_id, bot):
        return
    
    # پروفایل کاربر
    if handle_profile(text, chat_type, sender_id, message_id, chat_id, bot):
        return

    if handle_profile_reply(text, message, chat_type, sender_id, message_id, chat_id, bot):
        return

    # لیدربرد میو پوینت
    if handle_top_points(text, chat_type, sender_id, message_id, chat_id, bot):
        return

    # لیدربرد میو میو
    if handle_top_meows(text, chat_type, sender_id, message_id, chat_id, bot):
        return

    # پیوستن به گروه (سرزمین میویی)
    if handle_join_group(text, chat_type, sender_id, message_id, chat_id, bot):
        return

    # لیدربرد سرزمینی (پوینت)
    if handle_land_points_leaderboard(text, chat_type, sender_id, message_id, chat_id, bot):
        return

    # لیدربرد سرزمینی (میو)
    if handle_land_meows_leaderboard(text, chat_type, sender_id, message_id, chat_id, bot):
        return
    
    if handle_leave_group(text, chat_type, sender_id, message_id, chat_id, bot):
        return

    # انتقال پوینت (pay)
    if handle_pay(text, message, sender_id, message_id, chat_id, bot):
        return

    # بازی شرط‌بندی فوتبال
    if handle_soccer(text, sender_id, message_id, chat_id, bot):
        return
    if handle_soccer_stats(text, sender_id, message_id, chat_id, bot):
        return
    if handle_soccer_leaderboard(text, sender_id, message_id, chat_id, bot):
        return

    # بازی تاس
    if handle_dice(text, sender_id, message_id, chat_id, bot):
        return

    # بازی بسکتبال
    if handle_basketball(text, sender_id, message_id, chat_id, bot):
        return

    # بازی والیبال
    if handle_volleyball(text, sender_id, message_id, chat_id, bot):
        return

    # بازی ماهیگیری
    if handle_fishing(text, sender_id, message_id, chat_id, bot):
        return
    if handle_fish_inventory(text, sender_id, message_id, chat_id, bot):
        return
    if handle_sell_fish_start(text, sender_id, message_id, chat_id, bot):
        return
    if handle_fishing_stats(text, sender_id, message_id, chat_id, bot):
        return
    if handle_fishing_leaderboard(text, sender_id, message_id, chat_id, bot):
        return

    # سیستم پیشی (Pet)
    if handle_pet(text, sender_id, message_id, chat_id, bot):
        return
    if handle_feed_pet(text, sender_id, message_id, chat_id, bot):
        return
    if handle_collect_pet(text, sender_id, message_id, chat_id, bot):
        return
    if handle_upgrade_pet(text, sender_id, message_id, chat_id, bot):
        return
    if handle_rankup_pet(text, sender_id, message_id, chat_id, bot):
        return
    if handle_rename_pet(text, sender_id, message_id, chat_id, bot):
        return

    # یخچال میویی
    if handle_fridge_view(text, sender_id, message_id, chat_id, bot):
        return
    if handle_fridge_store_start(text, sender_id, message_id, chat_id, bot):
        return
    if handle_fridge_cook_start(text, sender_id, message_id, chat_id, bot):
        return
    if handle_fridge_sell_start(text, sender_id, message_id, chat_id, bot):
        return
    if handle_fridge_feed_start(text, sender_id, message_id, chat_id, bot):
        return
    if handle_fridge_upgrade(text, sender_id, message_id, chat_id, bot):
        return

    # پیشی‌ های خیابونی
    if handle_rescue_attempt(text, chat_type, sender_id, message_id, chat_id, bot):
        return
    if handle_kindness_leaderboard(text, chat_type, sender_id, message_id, chat_id, bot):
        return

    # بانک میویی
    if handle_bank_entry(text, sender_id, message_id, chat_id, bot):
        return
    if handle_bank_deposit(text, sender_id, message_id, chat_id, bot):
        return
    if handle_bank_withdraw(text, sender_id, message_id, chat_id, bot):
        return
    if handle_bank_change_number(text, sender_id, message_id, chat_id, bot):
        return
    if handle_bank_transfer(text, sender_id, message_id, chat_id, bot):
        return

    # کارخونه میویی
    if handle_factory_entry(text, sender_id, message_id, chat_id, bot):
        return
    if handle_hire_worker(text, sender_id, message_id, chat_id, bot):
        return
    if handle_fire_worker(text, sender_id, message_id, chat_id, bot):
        return
    if handle_start_production(text, sender_id, message_id, chat_id, bot):
        return
    if handle_upgrade_warehouse(text, sender_id, message_id, chat_id, bot):
        return
    if handle_upgrade_machine(text, sender_id, message_id, chat_id, bot):
        return
    if handle_sell_start(text, sender_id, message_id, chat_id, bot):
        return
    if handle_market_view(text, sender_id, message_id, chat_id, bot):
        return

    # قاچاق میویی
    if handle_smuggling_entry(text, sender_id, message_id, chat_id, bot):
        return
    if handle_start_smuggling(text, sender_id, message_id, chat_id, bot):
        return

    # مارکت میویی
    if handle_market_entry(text, sender_id, message_id, chat_id, bot):
        return
    if handle_buy_street_cat(text, sender_id, message_id, chat_id, bot):
        return
    if handle_buy_worm(text, sender_id, message_id, chat_id, bot):
        return
    if handle_buy_level(text, sender_id, message_id, chat_id, bot):
        return
    if handle_use_worm(text, sender_id, message_id, chat_id, bot):
        return

    # لیدربرد شهرهای پیشی (گروه در برابر گروه)
    if handle_loud_city_leaderboard(text, sender_id, message_id, chat_id, bot):
        return
    if handle_population_city_leaderboard(text, sender_id, message_id, chat_id, bot):
        return
    if handle_treasury_city_leaderboard(text, sender_id, message_id, chat_id, bot):
        return
    if handle_fish_market_city_leaderboard(text, sender_id, message_id, chat_id, bot):
        return
    
    if handle_shop_entry(text,sender_id,message_id,chat_id,bot):
        return
    if handle_shop_buy(text,sender_id,message_id,chat_id,bot):
        return
    if handle_shop_buy_with_wallet(text,sender_id,message_id,chat_id,bot):
        return
    if handle_wallet_charge(text,sender_id,message_id,chat_id,bot):
        return
    if handle_wallet_balance(text,sender_id,message_id,chat_id,bot):
        return
    if handle_shop_check(text,sender_id,message_id,chat_id,bot):
        return
    # ============ ابتدا پاسخ هلپر در گروه هلپرها ============
    if handle_answer_command(text, sender_id, message_id, chat_id, bot):
        return

    # ============ هندلرهای کاربری ============
    if handle_helpme(text, sender_id, message_id, chat_id, bot):
        return
    if handle_rate_ticket(text, sender_id, message_id, chat_id, bot):
        return
    if handle_my_tickets(text, sender_id, message_id, chat_id, bot):
        return
    # راهنما
    if handle_help(text, chat_type, sender_id, message_id, chat_id, bot):
        return
    
    if handle_get_user_role(text, message, sender_id, message_id, chat_id, bot):
        return
    
    if handle_use_gift(text, sender_id, message_id, chat_id, bot):
        return
    
    if handle_generate_invite(text, sender_id, message_id, chat_id, bot):
        return

    if handle_use_invite(text, sender_id, message_id, chat_id, bot):
        return

    if handle_my_invite(text, sender_id, message_id, chat_id, bot):
        return

    if handle_invite_leaderboard(text, sender_id, message_id, chat_id, bot):
        return
    
    if sender_id in ADMIN_ID:  # ADMIN_ID باید لیستی از شناسه‌ها باشد
        
    # پیام همگانی
        if handle_broadcast(message,text,sender_id,bot,chat_id,message_id):
            return
        
        if handle_broadcast_groups(message,text, sender_id, bot, chat_id, message_id):
            return
        
        # ارسال پول برای همه
        if handle_payall(text, message, sender_id, message_id, chat_id, bot):
            return
        
            # افزایش سطح (ادمین)
        if give_level(text, message, sender_id, message_id, chat_id, bot):
            return

        # کاهش سطح (ادمین)
        if remove_level(text, message, sender_id, message_id, chat_id, bot):
            return

        # افزایش پوینت (ادمین)
        if give_points(text, message, sender_id, message_id, chat_id, bot):
            return

        # کاهش پوینت (ادمین)
        if remove_points(text, message, sender_id, message_id, chat_id, bot):
            return
        
        if give_xp(text, message, sender_id, message_id, chat_id, bot):
            return

        if remove_xp(text, message, sender_id, message_id, chat_id, bot):
            return
        
        if give_meow(text, message, sender_id, message_id, chat_id, bot):
            return
        
        if remove_meow(text, message, sender_id, message_id, chat_id, bot):
            return
        
        if handle_set_role(text, message, sender_id, message_id, chat_id, bot):
            return

        if handle_remove_role(text, message, sender_id, message_id, chat_id, bot):
            return
        
        if handle_create_gift(text, sender_id, message_id, chat_id, bot):
            return
        if handle_list_gifts(text, sender_id, message_id, chat_id, bot):
            return
        if handle_delete_gift(text, sender_id, message_id, chat_id, bot):
            return
        
        if handle_helper_stats(text, sender_id, message_id, chat_id, bot):
            return
        if handle_helper_leaderboard(text, sender_id, message_id, chat_id, bot):
            return
        if get_message_data(text, message, sender_id, message_id, chat_id, bot):
            return


def get_my_ids(chat_id: str, message: dict , bot: API):
    bot.sendMessage(chat_id,f"آیدی شما: `{message['sender_id']}`")


def edited_message(update: dict, bot: API):
    chat_id: str = update.get('chat_id')
    chat_type: str = get_chat_type(chat_id)
    message = update.get('updated_message', {})
    if not int(message.get('time', 0)) > bot.time_run:
        return
    text = message.get('text', None)
    if not text:
        return
    message_id = message.get("message_id", None)
    sender_id = message.get('sender_id', None) 
    if  text == "myid":
        get_my_ids(chat_id,message,bot)
    
    if handle_antilink(sender_id,text, chat_type, chat_id, message_id, bot):
        return
        
def main():
    api = API(BOT_TOKEN)
    api.add_handler(NewMessageHandler(new_message))
    api.add_handler(EditedMessageHandler(edited_message))

    try:
        start_daramet_listener(DARAMET_USERNAME,DARAMET_TOKEN)
        api.run()
    except KeyboardInterrupt:
        print("\nربات متوقف شد")
    finally:
        db.exit()
        print("دیتابیس بسته شد")


if __name__ == "__main__":
    main()
