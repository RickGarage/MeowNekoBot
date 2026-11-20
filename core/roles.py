# core/roles.py
"""سیستم نقش‌های کاربری (Member, Helper, Special, Premium)"""

from core.db_instance import db

# لیست نقش‌های معتبر
VALID_ROLES = ["member", "helper", "special", "premium"]

# ترتیب اهمیت نقش‌ها (هرچه ایندکس بیشتر، اهمیت بالاتر)
ROLE_HIERARCHY = {
    "member": 0,
    "helper": 1,
    "special": 2,
    "premium": 3,
}


def get_user_role(user_id: str) -> str:
    """
    دریافت نقش فعلی کاربر
    
    Args:
        user_id: شناسه کاربر
        
    Returns:
        str: نام نقش (در صورت نداشتن، 'member' برگردانده می‌شود)
    """
    user_data = db.get_key(user_id, {})
    return user_data.get("role", "member").lower()


def set_user_role(user_id: str, role: str) -> bool:
    """
    تنظیم نقش برای کاربر (فقط نقش‌های معتبر)
    
    Args:
        user_id: شناسه کاربر
        role: نام نقش (member, helper, special, premium)
        
    Returns:
        bool: موفقیت‌آمیز بودن عملیات
    """
    if role and role.lower() not in VALID_ROLES:
        return False
    
    user_data = db.get_key(user_id, {})
    if role:
        user_data["role"] = role.lower()
    else:
        user_data["role"] = "member"  # نقش پیش‌فرض
    
    db.set_key(user_id, user_data)
    return True


def ensure_member_role(user_id: str) -> None:
    """
    اطمینان از اینکه کاربر نقش member را دارد (در صورت نداشتن، تنظیم می‌کند)
    
    Args:
        user_id: شناسه کاربر
    """
    user_data = db.get_key(user_id, {})
    if "role" not in user_data:
        user_data["role"] = "member"
        db.set_key(user_id, user_data)


def has_role(user_id: str, role: str) -> bool:
    """
    بررسی اینکه کاربر نقش مشخصی دارد
    
    Args:
        user_id: شناسه کاربر
        role: نام نقش مورد نظر
        
    Returns:
        bool: دارد / ندارد
    """
    return get_user_role(user_id) == role.lower()


def has_any_role(user_id: str, roles: list) -> bool:
    """
    بررسی اینکه کاربر حداقل یکی از نقش‌های لیست را دارد
    
    Args:
        user_id: شناسه کاربر
        roles: لیست نقش‌ها
        
    Returns:
        bool: دارد / ندارد
    """
    user_role = get_user_role(user_id)
    return user_role in [r.lower() for r in roles]


def is_role_higher(role1: str, role2: str) -> bool:
    """
    بررسی اینکه نقش اول از نقش دوم بالاتر است
    
    Args:
        role1: نقش اول
        role2: نقش دوم
        
    Returns:
        bool: بالاتر است / نیست
    """
    return ROLE_HIERARCHY.get(role1.lower(), 0) > ROLE_HIERARCHY.get(role2.lower(), 0)


def get_role_hierarchy_level(role: str) -> int:
    """
    دریافت سطح اهمیت نقش
    
    Args:
        role: نام نقش
        
    Returns:
        int: سطح (۰ اگر نقش معتبر نباشد)
    """
    return ROLE_HIERARCHY.get(role.lower(), 0)


def get_all_users_with_role(role: str) -> list:
    """
    دریافت لیست همه کاربرانی که نقش مشخصی دارند
    
    Args:
        role: نام نقش
        
    Returns:
        list: لیست شناسه کاربران
    """
    all_users = db.get_all_keys()
    result = []
    for uid in all_users:
        if uid.startswith('u') or uid.startswith('b'):
            user_data = db.get_key(uid, {})
            if user_data.get("role", "member").lower() == role.lower():
                result.append(uid)
    return result


def get_role_display_name(role: str) -> str:
    """
    دریافت نام نمایشی نقش به فارسی
    
    Args:
        role: نام نقش (member, helper, special, premium)
        
    Returns:
        str: نام فارسی نقش
    """
    role_map = {
        "member": "👤 عضو",
        "helper": "🤝 هلپر",
        "special": "⭐️ ویژه",
        "premium": "💎 پریمیوم",
    }
    return role_map.get(role.lower(), role)


def get_role_emoji(role: str) -> str:
    """
    دریافت ایموجی مربوط به نقش
    
    Args:
        role: نام نقش
        
    Returns:
        str: ایموجی نقش
    """
    emoji_map = {
        "member": "👤",
        "helper": "🛟",
        "special": "⭐",
        "premium": "💎",
    }
    return emoji_map.get(role.lower(), "")


def get_role_description(role: str) -> str:
    """
    دریافت توضیح مختصر درباره نقش
    
    Args:
        role: نام نقش
        
    Returns:
        str: توضیح نقش
    """
    desc_map = {
        "member": "کاربر عادی که ربات را استارت کرده",
        "helper": "کمک‌کننده و راهنمای ربات",
        "special": "کاربر ویژه با امکانات بیشتر",
        "premium": "کاربر پریمیوم با تمام امکانات",
    }
    return desc_map.get(role.lower(), "")


def get_user_role_info(user_id: str) -> dict:
    """
    دریافت اطلاعات کامل نقش کاربر
    
    Args:
        user_id: شناسه کاربر
        
    Returns:
        dict: شامل role, display_name, emoji, description, level
    """
    role = get_user_role(user_id)
    return {
        "role": role,
        "display_name": get_role_display_name(role),
        "emoji": get_role_emoji(role),
        "description": get_role_description(role),
        "level": get_role_hierarchy_level(role),
    }