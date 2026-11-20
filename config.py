# config.py
"""تنظیمات ثابت ربات میویی"""

ADMIN_ID = ["u0---"]
HELP_GROUP_CHAT_ID = "g0---"
BOT_TOKEN = "..."

LEVEL_CONFIG = {
    1: {'meows_needed': 0, 'points_range': (5, 15), 'cooldown': 300, 'bonus': 0},
    2: {'meows_needed': 5, 'points_range': (10, 20), 'cooldown': 297, 'bonus': 50},
    3: {'meows_needed': 15, 'points_range': (15, 25), 'cooldown': 294, 'bonus': 225},
    4: {'meows_needed': 40, 'points_range': (20, 35), 'cooldown': 291, 'bonus': 500},
    5: {'meows_needed': 75, 'points_range': (25, 40), 'cooldown': 288, 'bonus': 1000},
    6: {'meows_needed': 115, 'points_range': (35, 50), 'cooldown': 285, 'bonus': 1750},
    7: {'meows_needed': 175, 'points_range': (50, 75), 'cooldown': 282, 'bonus': 2500},
    8: {'meows_needed': 250, 'points_range': (75, 100), 'cooldown': 279, 'bonus': 3450},
    9: {'meows_needed': 350, 'points_range': (100, 125), 'cooldown': 276, 'bonus': 4625},
    10: {'meows_needed': 475, 'points_range': (125, 175), 'cooldown': 273, 'bonus': 6000},
    11: {'meows_needed': 625, 'points_range': (150, 225), 'cooldown': 270, 'bonus': 7500},
    12: {'meows_needed': 800, 'points_range': (175, 275), 'cooldown': 267, 'bonus': 9250},
    13: {'meows_needed': 975, 'points_range': (200, 325), 'cooldown': 264, 'bonus': 11250},
    14: {'meows_needed': 1175, 'points_range': (225, 375), 'cooldown': 261, 'bonus': 13400},
    15: {'meows_needed': 1400, 'points_range': (250, 425), 'cooldown': 258, 'bonus': 15750},
    16: {'meows_needed': 1650, 'points_range': (275, 475), 'cooldown': 255, 'bonus': 18250},
    17: {'meows_needed': 1925, 'points_range': (300, 525), 'cooldown': 252, 'bonus': 21000},
    18: {'meows_needed': 2225, 'points_range': (325, 575), 'cooldown': 249, 'bonus': 24000},
    19: {'meows_needed': 2550, 'points_range': (350, 625), 'cooldown': 246, 'bonus': 27250},
    20: {'meows_needed': 2900, 'points_range': (375, 675), 'cooldown': 243, 'bonus': 30500},
    21: {'meows_needed': 3275, 'points_range': (400, 725), 'cooldown': 240, 'bonus': 34000},
    22: {'meows_needed': 3675, 'points_range': (425, 775), 'cooldown': 237, 'bonus': 37750},
    23: {'meows_needed': 4100, 'points_range': (450, 825), 'cooldown': 234, 'bonus': 41750},
    24: {'meows_needed': 4550, 'points_range': (475, 875), 'cooldown': 231, 'bonus': 45850},
    25: {'meows_needed': 5000, 'points_range': (500, 925), 'cooldown': 228, 'bonus': 50250},
    26: {'meows_needed': 5525, 'points_range': (525, 975), 'cooldown': 225, 'bonus': 55000},
    27: {'meows_needed': 6050, 'points_range': (550, 1025), 'cooldown': 222, 'bonus': 60000},
    28: {'meows_needed': 7175, 'points_range': (575, 1075), 'cooldown': 219, 'bonus': 65000},
    29: {'meows_needed': 7775, 'points_range': (600, 1125), 'cooldown': 216, 'bonus': 70000},
    30: {'meows_needed': 8400, 'points_range': (625, 1175), 'cooldown': 213, 'bonus': 75000},
    31: {'meows_needed': 9050, 'points_range': (650, 1225), 'cooldown': 210, 'bonus': 80500},
    32: {'meows_needed': 9725, 'points_range': (675, 1275), 'cooldown': 207, 'bonus': 86500},
    33: {'meows_needed': 10425, 'points_range': (700, 1325), 'cooldown': 204, 'bonus': 92500},
    34: {'meows_needed': 11500, 'points_range': (725, 1375), 'cooldown': 201, 'bonus': 98500},
    35: {'meows_needed': 12000, 'points_range': (750, 1425), 'cooldown': 198, 'bonus': 105000},
    36: {'meows_needed': 12775, 'points_range': (800, 1475), 'cooldown': 195, 'bonus': 111500},
    37: {'meows_needed': 13475, 'points_range': (850, 1525), 'cooldown': 192, 'bonus': 118750},
    38: {'meows_needed': 14300, 'points_range': (900, 1575), 'cooldown': 189, 'bonus': 126000},
    39: {'meows_needed': 15150, 'points_range': (950, 1625), 'cooldown': 186, 'bonus': 134000},
    40: {'meows_needed': 16025, 'points_range': (1000, 1675), 'cooldown': 183, 'bonus': 142000},
    41: {'meows_needed': 16925, 'points_range': (1050, 1725), 'cooldown': 180, 'bonus': 150000},
    42: {'meows_needed': 17850, 'points_range': (1100, 1775), 'cooldown': 177, 'bonus': 158500},
    43: {'meows_needed': 18800, 'points_range': (1150, 1800), 'cooldown': 174, 'bonus': 167500},
    44: {'meows_needed': 19775, 'points_range': (1200, 1900), 'cooldown': 171, 'bonus': 176500},
    45: {'meows_needed': 20775, 'points_range': (1250, 2000), 'cooldown': 168, 'bonus': 186000},
    46: {'meows_needed': 21800, 'points_range': (1300, 2100), 'cooldown': 165, 'bonus': 195500},
    47: {'meows_needed': 22850, 'points_range': (1350, 2200), 'cooldown': 162, 'bonus': 205750},
    48: {'meows_needed': 23925, 'points_range': (1400, 2300), 'cooldown': 159, 'bonus': 216000},
    49: {'meows_needed': 25000, 'points_range': (1450, 2400), 'cooldown': 156, 'bonus': 226750},
    50: {'meows_needed': 27500, 'points_range': (1500, 2500), 'cooldown': 150, 'bonus': 250000},
}

MAX_LEVEL = 50

GAMELS_MIN_USER_LEVEL = 3
PAY_MIN_USER_LEVEL = 3
JOINING_MIN_USER_LEVEL = 2
FISHING_MIN_USER_LEVEL = 3



# ============ تنظیمات پیشی (Pet) ============
PET_PRICE = 30000              # هزینه خرید اولین پیشی
PET_MIN_USER_LEVEL = 3         # حداقل سطح کاربر برای خرید پیشی

PET_BASE_RATE_PER_SEC = 0.1    # تولید پوینت هر ثانیه در هر سطح (سطح 1 = 0.1)
PET_BASE_CAPACITY = 1000       # ظرفیت جعبه به ازای هر سطح و هر مقام
PET_LEVELS_PER_RANK = 5        # سقف سطح در هر مقام (5 تا در هر مقام باز میشه)

PET_UPGRADE_BASE_COST = 800    # ضریب هزینه ارتقا سطح (هزینه = این عدد × سطح فعلی)
PET_RANKUP_BASE_COST = 8000    # ضریب هزینه ارتقا مقام (هزینه = این عدد × مقام فعلی)

PET_FEED_ENERGY_SECONDS = 7200     # هر وعده غذا 2 ساعت انرژی میده
PET_BASE_MAX_ENERGY_MEALS = 3      # حداکثر تعداد وعده‌ای که میشه از قبل ذخیره کرد (مقام 1)
PET_EXTRA_MEALS_PER_RANK = 2       # به ازای هر مقام بالاتر، چند وعده ظرفیت شکم بیشتر میشه

# ============ تنظیمات یخچال میویی ============
FRIDGE_UNLOCK_LEVEL = 5            # سطح لازم برای فعال شدن یخچال
FRIDGE_BASE_CAPACITY = 2           # ظرفیت اولیه (تعداد نوع ماهی قابل ذخیره)
FRIDGE_UPGRADE_COST_BASE = 3000    # هزینه ارتقا = این عدد × ظرفیت فعلی

COOK_SECONDS_PER_001KG = 1         # هر 0.01 کیلوگرم وزن ماهی = 1 ثانیه زمان پخت
COOK_SELL_MULTIPLIER = 10          # قیمت فروش ماهی پخته‌شده 10 برابر میشه
COOK_FEED_MULTIPLIER = 2           # قدرت سیرکنندگی ماهی پخته‌شده 2 برابر میشه

# ============ تنظیمات بانک میویی ============
BANK_MIN_LEVEL = 4
BANK_OPEN_COST = 5000
BANK_CHANGE_NUMBER_COST = 1250
BANK_CHANGE_NUMBER_COOLDOWN = 72 * 3600     # 72 ساعت

BANK_DAILY_INTEREST_RATE = 0.03             # 3٪ سود روزانه
BANK_MAX_DAILY_INTEREST = 325000            # سقف سود روزانه

BANK_TRANSFER_FEE_RATE = 0.02               # 2٪ کارمزد کارت‌به‌کارت
BANK_TRANSFER_FEE_MIN = 100
BANK_TRANSFER_FEE_MAX = 10000


# ============ تنظیمات کارخونه میویی ============
FACTORY_MIN_LEVEL = 7
FACTORY_BUILD_COST = 2000000

WAREHOUSE_BASE_CAPACITY = 50
WAREHOUSE_CAPACITY_PER_LEVEL = 50
WAREHOUSE_UPGRADE_COST_BASE = 400000

MACHINE_BASE_CYCLE_SECONDS = 60
MACHINE_CYCLE_REDUCTION_PER_LEVEL = 5
MACHINE_MIN_CYCLE_SECONDS = 10
MACHINE_UPGRADE_COST_BASE = 100000

FACTORY_LEVEL_EXP_BASE = 1000        # آستانه سطح بعدی = این عدد × سطح فعلی

# محصولات کارخونه: unlock_level بر اساس سطح خودِ کارخونه است (نه سطح کاربر)
FACTORY_PRODUCTS = {
    'cat_food':        {'name': '🥫 جعبه غذای گربه',   'base_price': 800,   'unlock_level': 1, 'exp': 5},
    'mouse_toy':       {'name': '🐭 اسباب‌بازی موشی',  'base_price': 2000,  'unlock_level': 3, 'exp': 12},
    'luxury_bed':      {'name': '🛏 تخت پیشی لوکس',    'base_price': 5000,  'unlock_level': 5, 'exp': 30},
    'diamond_collar':  {'name': '💎 طوق الماس‌نشون',   'base_price': 15000, 'unlock_level': 8, 'exp': 80},
}

# ============ تنظیمات موتور بازار (نوسان قیمت) ============
MARKET_UPDATE_INTERVAL_SECONDS = 3600   # هر 1 ساعت قیمت‌ها آپدیت میشه

MARKET_MULT_MIN = 0.5
MARKET_MULT_MAX = 2.0
MARKET_MULT_REVERSION = 0.1             # هر ساعت به سمت 1.0 برمیگرده (میانگین‌گرا)
MARKET_MULT_NOISE = 0.15                # حداکثر نوسان تصادفی هر ساعت

ECONOMY_MULT_MIN = 0.7
ECONOMY_MULT_MAX = 1.6
ECONOMY_REFERENCE_AVG_WEALTH = 50000    # میانگین ثروت مرجع؛ بالاتر از این = تورم قیمت‌ها

# ============ تنظیمات قاچاق میویی ============
SMUGGLING_MIN_LEVEL = 6
SMUGGLING_MIN_CATS = 3
SMUGGLING_MAX_CATS = 15

SMUGGLING_SECONDS_PER_CAT = 120         # هر پیشی اضافه، 2 دقیقه به زمان ماموریت اضافه می‌کنه

SMUGGLING_REWARD_MIN_PER_CAT = 12500
SMUGGLING_REWARD_MAX_PER_CAT = 24000

SMUGGLING_BASE_CATCH_CHANCE = 0.05      # ریسک لو رفتن در حداقل تعداد (3 پیشی)
SMUGGLING_CATCH_CHANCE_PER_CAT = 0.035  # به ازای هر پیشی اضافه، ریسک لو رفتن بیشتر میشه
SMUGGLING_MAX_CATCH_CHANCE = 0.60

SMUGGLING_JAIL_DURATION = 1800          # 30 دقیقه زندان در صورت لو رفتن

# ============ تنظیمات مارکت میویی (خرید پیشی خیابونی و کرم ماهیگیری) ============
MARKET_CITY_LEVEL_REQUIRED = 7          # سطح شهر لازم برای باز شدن مارکت
MARKET_DAILY_LIMIT = 50                 # سقف خرید روزانه هر کاربر (مجموع همه آیتم‌ها)

MARKET_STREET_CAT_PRICE = 8000
MARKET_WORM_PRICE = 500
LEVEL_ITEM_PRICE = 15_000_000

# ============ تنظیمات آنتی اسپم ============
USER_SPAM_LIMIT = 5   # تعداد مجاز پیام در بازه زمانی
SPAM_WINDOW = 10       # بازه زمانی بر حسب ثانیه
SPAM_BAN_DURATION = 900  # 15 دقیقه به ثانیه


# ============ تنظیمات محصولات فروشگاه ============
# config.py (تنظیمات محصولات فروشگاه - اضافه کردن آیتم level)

SHOP_PRODUCTS = {
    "level": {
        "name": "افزایش سطح",
        "price_toman": 3500,
        "quantity": 1,
        "emoji": "✨",
        "description": "۱ سطح به سطح کاربر اضافه می‌کند"
    },
    "cat": {
        "name": "پیشی خیابونی",
        "price_toman": 10000,
        "quantity": 10,
        "emoji": "🐈",
        "description": "۱۰ تا پیشی خیابونی بامزه"
    },
    "meow": {
        "name": "میو",
        "price_toman": 15000,
        "quantity": 25,
        "emoji": "🐈",
        "description": "۲۵ تا میو"
    },
    "point": {
        "name": "میو پوینت ویژه",
        "price_toman": 2000,
        "quantity": 10000000,
        "emoji": "💎",
        "description": "۱۰ میلیون میو پوینت"
    },
    "special_role": {
        "name": "نقش ویژه",
        "price_toman": 50000,
        "quantity": 1,
        "emoji": "⭐",
        "description": "دریافت نقش ویژه (Special)",
        "role": "special"
    },
    "premium_role": {
        "name": "نقش پریمیوم",
        "price_toman": 100000,
        "quantity": 1,
        "emoji": "💎",
        "description": "دریافت نقش پریمیوم (Premium)",
        "role": "premium"
    }
}

FORBIDDEN_CODE_WORDS = []

DARAMET_TOKEN = "..."
DARAMET_USERNAME = "..."

REFERRAL_MIN_LEVEL = 10
REFERRAL_REWARD_POINTS = 10000
REFERRAL_REWARD_WALLET = 1000

# ============ کلیدواژه‌های میو ============
MEOW_KEYWORDS = [
    "میو", "میو میو", "meow", "meow meow",
    "ماعو", "معو", "میاعو", "maoo", "miao", "میعاو",
    "میعاعو", "مییاووو", "ماو","مع"
]

START_MESSAGE = """
🐾 ربات سرگرمی میویی 🐱

🐈 یه پیشی بامزه برای سرگرمی…
 کافیه توی گروه میو میو کنی تا میو پوینت بگیری 😸
 
⭐️ میو پوینت جمع کن و با بقیه رقابت کن
🏆 لیدربرد میویی رو فتح کن و پادشاه پیشی‌ ها شو

✨ چرا میویی ؟

⚡ پاسخگویی فوق‌ العاده سریع
🛠️ عملکرد پایدار و بدون باگ
🔄 آپدیت‌ های هفتگی
👥 کامیونیتی فعال و پرانرژی
🚨 پشتیبانی ۲۴ ساعته
🪙 کاملاً رایگان برای همه

🐱 کافیه ربات رو عضو گروهت کنی و مدیرش کنی…
┘─ بعدش شروع کنی به میو میو کردن

لینک گروه پیشنهادی:
https://rubika.ir/joing/BBEJIAIAI0GSTPANQWVRQMHFFSQRWPUS
"""

HELP_MESSAGE = """
📋 راهنمای ربات میویی 🐱

⚡️ کامندهای موجود:

1️⃣ میو کردن:
   • میو / meow / miao
   • دریافت پوینت تصادفی

2️⃣ پروفایل:
   • میو هام / mymeows / پروفایل
   • نمایش آمار و رتبه شما

3️⃣ لیدربرد:
   • لیدربرد پوینت / top points
   • نمایش ثروتمندترین ها
   
   • لیدربرد میو / top meows
   • نمایش پر میو ترین ها
 
4️⃣ (از سطح 3)انتقال پوینت:
   • pay [مقدار] (روی پیام کاربر ریپلای کن)
   • انتقال پوینت به سایر کاربران
   • محدوده: 10 تا 100000 پوینت

5️⃣ (از سطح 2)سرزمین میویی 🏙:
   • پیوستن به گروه (داخل گروه بفرست)
   • به سرزمین (شهر) این گروه می‌پیوندی
   
   • لیدربرد سرزمین
   • ثروتمند ترین ساکنین سرزمین
   
   • لیدربرد سرزمین میو
   • پر سر و صدا ترین ساکنین سرزمین

6️⃣ (از سطح 3)ماهیگیری 🎣:
   • ماهیگیری
   • صید ماهی و ذخیره خودکار توی انبار
   
   • انبار ماهی / موجودی ماهی
   • مشاهده انبار و ارزش ماهی‌ها
   
   • فروش ماهی
   • شروع فرآیند فروش (کانورسیشن مرحله‌ای)
   
   • آمار ماهیگیری / لیدربرد ماهیگیری

7️⃣ (از سطح 3)پیشی 🐈:
   • پیشی
   • خرید پیشی اختصاصی (یا مشاهده وضعیتش اگه داری)
   
   • تغذیه پیشی / غذا پیشی
   • سیر کردن پیشی با ماهی‌های انبارت
   
   • برداشت پیشی
   • برداشت میو پوینت‌های جمع‌شده در جعبه
   
   • ارتقا سطح پیشی
   • بالا بردن سطح (سرعت تولید و ظرفیت بیشتر)
   
   • ارتقا مقام پیشی
   • تحول بزرگ! سقف سطح و ظرفیت شکم بیشتر میشه
   
   • اسم پیشی [نام دلخواه]
   • اسم گذاشتن روی پیشی‌ات

8️⃣ یخچال میویی ❄️ (از سطح 5):
   • یخچال / یخچال من
   • مشاهده یخچال و وضعیت ماهی‌ها
   
   • ذخیره یخچال
   • فریز کردن یه ماهی (فقط یکی از هر نوع)
   
   • پخت ماهی
   • ۱۰ برابر کردن قیمت فروش (زمان‌بر، بر اساس وزن)
   
   • فروش یخچال / تغذیه یخچال
   • فروش یا تغذیه پیشی با ماهی‌های ذخیره‌شده
   
   • ارتقا یخچال
   • افزایش ظرفیت یخچال

9️⃣ پیشی‌ های خیابونی 🐈 (داخل گروه):
   • با میو کردن اهالی شهر، گاهی یه پیشی خیابونی ظاهر میشه
   
   • نجات پیشی
   • تلاش برای نجاتش (شانس ۳۰٪، ۳ فرصت، ۵ دقیقه وقت)
   
   • لیدربرد مهربونی
   • رتبه‌ بندی نجات‌دهنده‌ های برتر

🔟 بانک میویی 🏦 (از سطح 4):
   • بانک میویی
   • افتتاح حساب یا مشاهده وضعیت
   
   • واریز [مقدار] / برداشت [مقدار]
   • جابجایی بین موجودی نقدی و بانک
   
   • کارت به کارت [شماره حساب] [مقدار]
   • انتقال به حساب دیگر (۲٪ کارمزد)
   
   • تغییر شماره حساب
   • هر ۷۲ ساعت یک‌بار، با هزینه

1️⃣1️⃣ کارخونه میویی 🏭 (از سطح 7):
   • کارخونه میویی
   • ساخت کارخونه یا مشاهده وضعیت
   
   • استخدام کارگر [عدد] / اخراج کارگر [عدد]
   • کارگرها از پیشی‌ های خیابونی نجات‌داده‌ ات میان
   
   • شروع تولید
   • انتخاب محصول برای تولید خودکار
   
   • فروش کارخونه
   • فروش محصولات با قیمت لحظه‌ ای بازار
   
   • بازار کارخونه / قیمت بازار
   • مشاهده نوسان قیمت‌ ها
   
   • ارتقا انبار / ارتقا دستگاه

1️⃣2️⃣ قاچاق میویی 🥷 (از سطح 6):
   • قاچاق میویی
   • پنل شروع/پیگیری ماموریت (با پیشی‌ های خیابونی آزادت)
   
   • شروع قاچاق [تعداد پیشی]
   • هرچی محموله بزرگ‌تر، پاداش و ریسک لو رفتن هر دو بیشتر

1️⃣3️⃣ مارکت میویی 🛍 (سطح شهر 7+):
   • مارکت میویی
   • مشاهده قیمت‌ ها و سهمیه روزانه
   
   • خرید پیشی [تعداد] / خرید کرم [تعداد]
   • استفاده از کرم (رفع فوری کول‌داون ماهیگیری)

1️⃣4️⃣ لیدربرد شهرهای پیشی 🏙 (گروه در برابر گروه):
   • لیدربرد شهر صدا — پرسروصداترین سرزمین‌ ها
   • لیدربرد شهر جمعیت — پرجمعیت‌ ترین (پیشی خیابونی)
   • لیدربرد شهر ثروت — ثروتمندترین (خزانه بانکی)
   • لیدربرد شهر ماهی — بهترین بازار ماهی

⭐️ هرچه سطح بالاتر:
   • پوینت بیشتر دریافت می‌کنی
   • زمان استراحت کمتر می‌شود
"""
