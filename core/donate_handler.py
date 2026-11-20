# core/donate_handler.py
"""پردازش خودکار دونیت‌های دریافتی از درگاه دارمت"""

from config import BOT_TOKEN
from libs.Daramet import Daramet, Donate
from core.db_instance import db
from core.shop import get_order_by_code, update_order_status, deliver_order_products


def process_donate(donate: Donate):
    print(f"""
    New donate:
    - from: {donate.donator}
    - amount: {donate.amount} Rial
    - message: {donate.message}
    """)
    try:
        code = donate.message.strip()
        amount_rial = donate.amount
        amount_toman = amount_rial // 10

        order = get_order_by_code(code)
        if not order:
            print(f"Order with code {code} not found!")
            return

        if order["status"] != "pending":
            print(f"Order {code} already processed")
            return

        user_id = order["user_id"]
        order_type = order.get("type", "product")

        if order_type == "wallet":
            required = order["amount_toman"]
            user_data = db.get_key(user_id, {})
            if amount_toman < required:
                user_data["wallet_balance"] = user_data.get("wallet_balance", 0) + amount_toman
                db.set_key(user_id, user_data)
                update_order_status(code, "partial", paid_amount=amount_toman)
                # send message to user
                user_chat_id = db.get_key(user_id, {}).get('chat_id')
                if user_chat_id:
                    try:
                        from rubik import API
                        bot = API(BOT_TOKEN)
                        bot.sendMessage(
                            user_chat_id,
                            f"⚠️ مبلغ پرداختی ({amount_toman:,} تومان) کمتر از مبلغ درخواستی ({required:,} تومان) است.\n"
                            f"💰 مبلغ واریزی به کیف پول شما اضافه شد.\n"
                            f"📌 برای شارژ کامل، مابقی رو پرداخت کن یا دوباره اقدام کن.\n"
                            f"🆔 کد: `{code}`"
                        )
                    except Exception as e:
                        print(f"Failed to send message to {user_id}: {e}")
                return

            # full or over payment
            user_data["wallet_balance"] = user_data.get("wallet_balance", 0) + required
            extra = amount_toman - required
            if extra > 0:
                user_data["wallet_balance"] += extra
            db.set_key(user_id, user_data)
            update_order_status(code, "delivered", paid_amount=amount_toman)

            # send success message
            user_chat_id = db.get_key(user_id, {}).get('chat_id')
            if user_chat_id:
                try:
                    from rubik import API
                    bot = API(BOT_TOKEN)
                    msg = f"✅ کیف پول شما با موفقیت شارژ شد!\n\n"
                    msg += f"💰 مبلغ شارژ: {required:,} تومان\n"
                    if extra > 0:
                        msg += f"➕ اضافه‌پرداخت: {extra:,} تومان به کیف پول اضافه شد.\n"
                    msg += f"📊 موجودی جدید: {user_data['wallet_balance']:,} تومان\n"
                    msg += f"🆔 کد: `{code}`"
                    bot.sendMessage(user_chat_id, msg)
                except Exception as e:
                    print(f"Failed to send wallet charge message: {e}")
            return

        # product order
        if amount_toman < order["amount_toman"]:
            # partial payment for product - add to wallet (or handle as you wish)
            user_data = db.get_key(user_id, {})
            user_data["wallet_balance"] = user_data.get("wallet_balance", 0) + amount_toman
            db.set_key(user_id, user_data)
            update_order_status(code, "partial", paid_amount=amount_toman)
            user_chat_id = db.get_key(user_id, {}).get('chat_id')
            if user_chat_id:
                try:
                    from rubik import API
                    bot = API(BOT_TOKEN)
                    bot.sendMessage(
                        user_chat_id,
                        f"⚠️ مبلغ پرداختی ({amount_toman:,} تومان) کمتر از مبلغ سفارش ({order['amount_toman']:,} تومان) است.\n"
                        f"💰 مبلغ به کیف پول شما اضافه شد.\n"
                        f"📌 برای تکمیل خرید، مابقی رو پرداخت کن یا با کیف پول خرید کن.\n"
                        f"🆔 کد: `{code}`"
                    )
                except Exception as e:
                    print(f"Failed to send partial payment message: {e}")
            return

        # full payment for product
        deliver_msg = deliver_order_products(order, user_id)
        update_order_status(code, "delivered", paid_amount=amount_toman)

        extra = amount_toman - order["amount_toman"]
        if extra > 0:
            user_data = db.get_key(user_id, {})
            user_data["wallet_balance"] = user_data.get("wallet_balance", 0) + extra
            db.set_key(user_id, user_data)

        user_chat_id = db.get_key(user_id, {}).get('chat_id')
        if user_chat_id:
            try:
                from rubik import API
                bot = API(BOT_TOKEN)
                msg = f"🎉 پرداخت شما با موفقیت تأیید شد!\n\n"
                msg += deliver_msg + "\n"
                if extra > 0:
                    msg += f"💰 اضافه‌پرداخت {extra:,} تومان به کیف پول شما اضافه شد.\n"
                msg += f"📊 موجودی کیف پول: {db.get_key(user_id, {}).get('wallet_balance', 0):,} تومان\n"
                msg += f"🆔 کد: `{code}`"
                bot.sendMessage(user_chat_id, msg)
            except Exception as e:
                print(f"Failed to send product delivery message: {e}")

        print(f"Order {code} completed for user {user_id}")

    except Exception as e:
        print(f"Unexpected error in process_donate: {e}")


def start_daramet_listener(username: str, token: str):
    try:
        daramet = Daramet(
            username=username,
            token=token,
            handler=process_donate,
            seconds_ago=3000
        )
        daramet.start()
        print(f"Daramet listener started for {username}")
        return daramet
    except Exception as e:
        print(f"Failed to start Daramet listener: {e}")
        return None