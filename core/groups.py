# core/groups.py
"""توابع مربوط به گروه ها (سرزمین های میویی) - عضویت و رتبه بندی داخل گروه"""

from core.db_instance import db


def _default_group_data(chat_id):
    return {
        'chat_id': chat_id,
        'title': None,
        'members': [],
        'created_at': None,
    }


def register_group(chat_id, bot=None):
    """اطمینان از وجود رکورد گروه در دیتابیس و به‌روزرسانی عنوان آن"""
    if not chat_id:
        return None

    group_data = db.get_key(chat_id, None)
    if not isinstance(group_data, dict):
        group_data = _default_group_data(chat_id)

    # تلاش برای به‌روزرسانی عنوان گروه (اگر بات در دسترس باشد)
    if bot is not None:
        try:
            chat_info = bot.getChat(chat_id)
            if chat_info and chat_info.title:
                group_data['title'] = chat_info.title
        except Exception:
            pass

    db.set_key(chat_id, group_data)
    return group_data


def get_group_data(chat_id):
    data = db.get_key(chat_id, None)
    if isinstance(data, dict):
        return data
    return None


def get_user_group(sender_id):
    """گروه (سرزمین) فعلی کاربر را برمی‌گرداند"""
    user_data = db.get_key(sender_id, {})
    if isinstance(user_data, dict):
        return user_data.get('group_id')
    return None


def join_group(sender_id, chat_id, bot=None):
    """
    کاربر را به یک گروه (سرزمین میویی) متصل می‌کند.

    Returns:
        tuple(bool, str): (موفقیت, کد وضعیت)
        کد وضعیت یکی از: 'joined', 'already_member', 'switched'
    """
    group_data = register_group(chat_id, bot)
    if group_data is None:
        return False, 'error'

    user_data = db.get_key(sender_id, {})
    if not isinstance(user_data, dict):
        user_data = {}

    previous_group = user_data.get('group_id')

    if previous_group == chat_id:
        return True, 'already_member'

    # حذف کاربر از عضویت گروه قبلی (در صورت وجود)
    if previous_group:
        old_group_data = get_group_data(previous_group)
        if old_group_data and sender_id in old_group_data.get('members', []):
            old_group_data['members'].remove(sender_id)
            db.set_key(previous_group, old_group_data)

    # افزودن کاربر به گروه جدید
    if sender_id not in group_data.get('members', []):
        group_data.setdefault('members', []).append(sender_id)
        db.set_key(chat_id, group_data)

    user_data['group_id'] = chat_id
    db.set_key(sender_id, user_data)

    return True, 'switched' if previous_group else 'joined'


def get_group_top_users(chat_id, by='points', limit=5):
    """دریافت برترین کاربران داخل یک گروه (سرزمین) خاص"""
    group_data = get_group_data(chat_id)
    if not group_data:
        return []

    user_list = []
    for uid in group_data.get('members', []):
        data = db.get_key(uid, {})
        if not isinstance(data, dict) or not data:
            continue

        # اگر کاربر دیگر عضو این گروه نیست (سوییچ کرده) نادیده بگیر
        if data.get('group_id') != chat_id:
            continue

        value = data.get('meow_points', 0) if by == 'points' else data.get('meow_count', 0)
        if value > 0:
            user_list.append((uid, value, data))

    user_list.sort(key=lambda x: x[1], reverse=True)
    return user_list[:limit]



def get_city_total_points(chat_id):
    """مجموع میو پوینت اعضای عضو این سرزمین (برای محاسبه سطح شهر)"""
    group_data = get_group_data(chat_id)
    if not group_data:
        return 0

    total = 0
    for uid in group_data.get('members', []):
        data = db.get_key(uid, {})
        if isinstance(data, dict) and data.get('group_id') == chat_id:
            total += data.get('meow_points', 0)
    return total


def get_city_level(chat_id):
    """
    سطح شهر (سرزمین) بر اساس مجموع ثروت اعضای عضوش.
    هر چی سطح بالاتر باشه، رویداد های ویژه (مثل ظاهر شدن پیشی خیابونی) بیشتر اتفاق می‌افتن.
    """
    total_points = get_city_total_points(chat_id)
    level = 1 + min(9, total_points // 50000)
    return int(level)


def get_all_group_chat_ids():
    """
    شناسه تمام گروه‌ های ثبت‌شده (سرزمین‌ ها) را برمی‌گرداند.
    توجه: چون chat_id گروه‌ ها با 'g' یا 's' شروع میشه و ممکنه با کلیدهای دیگه‌ ای مثل
    'soccer_history' تداخل حرف اول داشته باشه، برای اطمینان چک می‌کنیم که مقدار واقعاً
    یک دیکشنری داده گروهیه (دارای کلید 'members').
    """
    group_ids = []
    for key in db.get_all_keys():
        if not key or not (key.startswith('g') or key.startswith('s')):
            continue
        data = db.get_key(key, None)
        if isinstance(data, dict) and 'members' in data:
            group_ids.append(key)
    return group_ids


def get_group_rank(chat_id, sender_id, by='points'):
    """رتبه کاربر داخل لیدربرد سرزمین خودش"""
    group_data = get_group_data(chat_id)
    if not group_data:
        return "نامشخص"

    ranked = []
    for uid in group_data.get('members', []):
        data = db.get_key(uid, {})
        if not isinstance(data, dict) or not data:
            continue
        if data.get('group_id') != chat_id:
            continue
        value = data.get('meow_points', 0) if by == 'points' else data.get('meow_count', 0)
        if value > 0:
            ranked.append((uid, value))

    ranked.sort(key=lambda x: x[1], reverse=True)
    for idx, (uid, _) in enumerate(ranked, 1):
        if uid == sender_id:
            return f"{idx:,}"
    return "نامشخص"

def leave_group(user_id: str, group_id: str) -> bool:
    """
    خروج کاربر از گروه (سرزمین)
    """
    if not user_id or not group_id:
        return False

    user_data = db.get_key(user_id, {})
    current_group = user_data.get('group_id')
    if current_group != group_id:
        return False

    user_data.pop('group_id', None)
    db.set_key(user_id, user_data)

    # به‌روزرسانی آمار گروه
    group_data = get_group_data(group_id)
    if group_data:
        group_data['member_count'] = max(0, group_data.get('member_count', 0) - 1)
        db.set_key(f"group_{group_id}", group_data)

    return True


def get_group_stats(group_id: str) -> dict:
    """
    دریافت آمار گروه
    """
    group_data = get_group_data(group_id)
    if not group_data:
        return {
            'member_count': 0,
            'total_points': 0,
            'total_meows': 0,
            'avg_points': 0,
            'avg_meows': 0,
        }

    all_users = db.get_all_keys()
    members = []
    for uid in all_users:
        if not uid:
            continue
        if uid.startswith('u') or uid.startswith('b'):
            user_data = db.get_key(uid, {})
            if not isinstance(user_data,dict):
                continue
            if user_data.get('group_id') == group_id:
                members.append(user_data)

    total_points = sum(u.get('meow_points', 0) for u in members)
    total_meows = sum(u.get('meow_count', 0) for u in members)
    count = len(members)

    return {
        'member_count': count,
        'total_points': total_points,
        'total_meows': total_meows,
        'avg_points': total_points // count if count > 0 else 0,
        'avg_meows': total_meows // count if count > 0 else 0,
    }
