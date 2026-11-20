# database.py
import sqlite3
import json
from typing import Any, Optional

class Database:
    def __init__(self, db_path: str = "bot_data.db"):
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        self._connect()
        self._create_table()
    
    def _connect(self):
        """ایجاد اتصال به دیتابیس"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.connection.cursor()
        except sqlite3.Error as e:
            print(f"خطا در اتصال به دیتابیس: {e}")
            raise
    
    def _create_table(self):
        """ایجاد جدول اصلی برای ذخیره کلید-مقدار"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS kv_store (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"خطا در ایجاد جدول: {e}")
            raise
    
    def set_key(self, key: str, value: Any) -> bool:
        try:
            json_value = json.dumps(value, ensure_ascii=False)
            
            self.cursor.execute('''
                INSERT INTO kv_store (key, value, updated_at) 
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET 
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
            ''', (key, json_value))
            
            self.connection.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"خطا در ذخیره کلید {key}: {e}")
            self.connection.rollback()
            return False
        except json.JSONEncodeError as e:
            print(f"خطا در تبدیل مقدار به JSON: {e}")
            return False
    
    def get_key(self, key: str, default: Any = None) -> Optional[Any]:
        try:
            self.cursor.execute('SELECT value FROM kv_store WHERE key = ?', (key,))
            result = self.cursor.fetchone()
            
            if result:
                try:
                    return json.loads(result[0])
                except json.JSONDecodeError:
                    return result[0]
            return default
            
        except sqlite3.Error as e:
            print(f"خطا در دریافت کلید {key}: {e}")
            return default
    
    def remove(self, key: str) -> bool:
        try:
            self.cursor.execute('DELETE FROM kv_store WHERE key = ?', (key,))
            rows_affected = self.cursor.rowcount
            self.connection.commit()
            return rows_affected > 0
            
        except sqlite3.Error as e:
            print(f"خطا در حذف کلید {key}: {e}")
            self.connection.rollback()
            return False
    
    def exit(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            print("اتصال دیتابیس بسته شد.")
        except sqlite3.Error as e:
            print(f"خطا در بستن دیتابیس: {e}")
    
    def get_all_keys(self) -> list:
        try:
            self.cursor.execute('SELECT key FROM kv_store')
            return [row[0] for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"خطا در دریافت کلیدها: {e}")
            return []
    
    def clear_all(self) -> bool:
        try:
            self.cursor.execute('DELETE FROM kv_store')
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"خطا در پاک کردن داده‌ها: {e}")
            self.connection.rollback()
            return False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """خروج از context manager"""
        self.exit()
