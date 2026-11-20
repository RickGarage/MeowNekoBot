# core/db_instance.py
"""نمونه مشترک دیتابیس که در تمام هندلرها استفاده می‌شود"""

from database import Database

db = Database()
tickets = Database("tickets.db")
