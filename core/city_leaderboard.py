# core/city_leaderboard.py
"""لیدربرد شهرهای پیشی - رقابت گروه‌ ها (سرزمین‌ ها) با هم بر اساس چند معیار"""

from core.db_instance import db
from core.groups import get_all_group_chat_ids, get_group_data


def compute_city_stats(chat_id):
    """
    آمار تجمیعی یک سرزمین بر اساس اعضای فعلاً عضوش:
    - meow_count: مجموع تعداد میو (پرسروصداترین)
    - population: مجموع پیشی‌ های خیابونی نجات‌داده (پرجمعیت‌ ترین)
    - treasury: مجموع موجودی بانک اعضا (ثروتمندترین - به‌عنوان خزانه شهر)
    - fish_total: مجموع تعداد کل ماهی‌ های صید شده (بهترین بازار ماهی)
    """
    group_data = get_group_data(chat_id)
    if not group_data:
        return None

    stats = {'meow_count': 0, 'population': 0, 'treasury': 0, 'fish_total': 0, 'member_count': 0}

    for uid in group_data.get('members', []):
        data = db.get_key(uid, {})
        if not isinstance(data, dict) or not data:
            continue
        if data.get('group_id') != chat_id:
            continue

        stats['member_count'] += 1
        stats['meow_count'] += data.get('meow_count', 0)
        stats['population'] += data.get('rescued_cats_count', 0)
        stats['fish_total'] += data.get('fishing_total_fish', 0)

        bank = data.get('bank')
        if isinstance(bank, dict):
            stats['treasury'] += bank.get('balance', 0)

    return stats


def get_top_cities(metric, limit=5):
    """
    شهرهای برتر بر اساس یک معیار مشخص.

    Args:
        metric: یکی از 'meow_count', 'population', 'treasury', 'fish_total'

    Returns:
        list[tuple(chat_id, value, stats, title)] مرتب‌شده نزولی
    """
    results = []

    for chat_id in get_all_group_chat_ids():
        stats = compute_city_stats(chat_id)
        if not stats or stats['member_count'] == 0:
            continue

        value = stats.get(metric, 0)
        if value <= 0:
            continue

        group_data = get_group_data(chat_id)
        title = (group_data or {}).get('title') or "سرزمین ناشناس"

        results.append((chat_id, value, stats, title))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:limit]


def get_city_rank(chat_id, metric):
    """رتبه یک شهر مشخص در بین همه شهرها بر اساس یک معیار (بدون محدودیت تعداد)"""
    all_results = []

    for cid in get_all_group_chat_ids():
        stats = compute_city_stats(cid)
        if not stats or stats['member_count'] == 0:
            continue
        value = stats.get(metric, 0)
        if value <= 0:
            continue
        all_results.append((cid, value))

    all_results.sort(key=lambda x: x[1], reverse=True)

    for idx, (cid, _) in enumerate(all_results, 1):
        if cid == chat_id:
            return idx
    return None
