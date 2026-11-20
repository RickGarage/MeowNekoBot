
# rubik.py
from time import sleep, time
import requests
from requests import post
from enum import Enum
from abc import ABC
import json
import logging
from typing import Optional
from database import Database
from metadata import Track_parsed as GlyphWeaver


# CONSTS:

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db_message = Database("messages_bot.db")
db_tokenbots = Database("token_bots.db")



# ENUMS:


class ChatTypeEnum(Enum):
    """نوع چت"""
    PRIVATE = "Private"      # چت خصوصی
    GROUP = "Group"          # گروه
    CHANNEL = "Channel"      # کانال
    UNKNOWN = "Unknown"      # ناشناخته

def get_chat_type(chat_id: str) -> str:
    """
    تشخیص نوع چت بر اساس شناسه چت
    
    Args:
        chat_id: شناسه چت
        
    Returns:
        str: نوع چت
    """
    if not chat_id:
        return ChatTypeEnum.UNKNOWN.value
        
    if chat_id.startswith('g'):
        return ChatTypeEnum.GROUP.value
    elif chat_id.startswith('b'):
        return ChatTypeEnum.PRIVATE.value
    elif chat_id.startswith('c'):
        return ChatTypeEnum.CHANNEL.value
    elif chat_id.startswith('s'):
        return ChatTypeEnum.SUPERGROUP.value
    else:
        return ChatTypeEnum.UNKNOWN.value


        
class MessageSenderEnum(Enum):
    """نوع فرستنده پیام"""
    User = "User"      # کاربر
    Bot = "Bot"        # بات


class UpdateTypeEnum(Enum):
    """نوع آپدیت دریافتی"""
    UpdatedMessage = "UpdatedMessage"   # ویرایش پیام
    NewMessage = "NewMessage"           # پیام جدید
    RemovedMessage = "RemovedMessage"   # حذف پیام
    StartedBot = "StartedBot"           # شروع بات
    StoppedBot = "StoppedBot"           # توقف بات


# MODELS:


class ChatModel:
    """
    مدل اطلاعات چت
    
    Attributes:
        chat_id (str): شناسه چت
        chat_type (str): نوع چت (کاربر، گروه، کانال و …)
        user_id (Optional[str]): شناسه کاربر مقابل بات در چت‌های خصوصی است. (فقط در چت‌های خصوصی)
        first_name (Optional[str]): نام کاربر. (فقط در چت‌های خصوصی)
        last_name (Optional[str]): نام خانوادگی کاربر
        title (Optional[str]): عنوان گروه یا کانال (در چت‌های گروهی و کانال‌ها)
        username (Optional[str]): نام کاربری چت یا کاربر (در صورت تنظیم شدن)
    """
    
    def __init__(self, data: dict):
        """
        مقداردهی اولیه مدل چت
        
        Args:
            data: دیکشنری حاوی اطلاعات چت
        """
        self.chat_id: str = data.get('chat_id', "")
        self.chat_type: str = data.get('chat_type', get_chat_type(self.chat_id))
        self.user_id: Optional[str] = data.get('user_id', None)
        self.first_name: Optional[str] = data.get('first_name', None)
        self.last_name: Optional[str] = data.get('last_name', None)
        self.title: Optional[str] = data.get('title', None)
        self.username: Optional[str] = data.get('username', None)
    
    def is_private(self) -> bool:
        """بررسی اینکه چت خصوصی است یا خیر"""
        return self.chat_type == ChatTypeEnum.PRIVATE.value
    
    def is_group(self) -> bool:
        """بررسی اینکه چت گروهی است یا خیر"""
        return self.chat_type == ChatTypeEnum.GROUP.value
    
    def is_channel(self) -> bool:
        """بررسی اینکه چت کانال است یا خیر"""
        return self.chat_type == ChatTypeEnum.CHANNEL.value
    
    def get_display_name(self) -> str:
        """
        دریافت نام نمایشی چت
        
        Returns:
            str: نام نمایشی چت
        """
        if self.first_name:
            if self.last_name:
                return f"{self.first_name} {self.last_name}"
            return self.first_name
        elif self.title:
            return self.title
        elif self.username:
            return f"@{self.username}"
        return self.chat_id
    
    def get_full_name(self) -> Optional[str]:
        """
        دریافت نام کامل کاربر (فقط در چت‌های خصوصی)
        
        Returns:
            Optional[str]: نام کامل کاربر یا None
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
    
    def to_dict(self) -> dict:
        """
        تبدیل مدل به دیکشنری
        
        Returns:
            dict: دیکشنری حاوی اطلاعات چت
        """
        return {
            'chat_id': self.chat_id,
            'chat_type': self.chat_type,
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'title': self.title,
            'username': self.username
        }
    
    def __str__(self) -> str:
        """نمایش رشته‌ای از مدل"""
        display_name = self.get_display_name()
        return f"Chat({self.chat_id} - {self.chat_type}: {display_name})"
    
    def __repr__(self) -> str:
        """نمایش رسمی مدل"""
        return f"ChatModel(chat_id='{self.chat_id}', chat_type='{self.chat_type}')"


class BaseHandler(ABC):
    
    def __init__(self, callback):
        self.callback = callback

    def handle(self, update, api) -> None:
        callback = self.callback
        callback(update, api)

class NewMessageHandler(BaseHandler):
    def __init__(self, callback):
        super().__init__(callback)
        self.type = UpdateTypeEnum.NewMessage.value

class EditedMessageHandler(BaseHandler):
    def __init__(self, callback):
        super().__init__(callback)
        self.type = UpdateTypeEnum.UpdatedMessage.value


class API:
    
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://botapi.rubika.ir/v3/{token}/"
        self.offset_id = db_tokenbots.get_key(token)
        self.groups: list = db_message.get_key("groups_fix",[])
        
        self.running = False
        self.handlers = []
        self.time_run = int(time())
        self.max_retries = 3
        self.retry_delay = 5
    
    def add_handler(self, handler):
        self.handlers.append(handler)
    
    def _post(self, method, data={}, retry_count=0):
        """ارسال درخواست با مدیریت خطا"""
        try:
            url = self.base_url + method
            logger.info(f"POST Request: {url}")
            
            response = post(url, json=data, timeout=30)
            
            # بررسی وضعیت پاسخ
            if response.status_code != 200:
                logger.error(f"HTTP Error {response.status_code}: {response.text}")
                if retry_count < self.max_retries:
                    logger.info(f"Try in {retry_count + 1}/{self.max_retries}...")
                    sleep(self.retry_delay)
                    return self._post(method, data, retry_count + 1)
                return None
            
            # بررسی محتوای پاسخ
            if not response.text or response.text.strip() == '':
                logger.error("Error: Empty answer!")
                if retry_count < self.max_retries:
                    sleep(self.retry_delay)
                    return self._post(method, data, retry_count + 1)
                return None
            
            try:
                return response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Error in parse JSON: {e}")
                logger.error(f"Details of data: {response.text[:200]}")
                if retry_count < self.max_retries:
                    sleep(self.retry_delay)
                    return self._post(method, data, retry_count + 1)
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Error: timeout is done!")
            if retry_count < self.max_retries:
                sleep(self.retry_delay)
                return self._post(method, data, retry_count + 1)
            return None
            
        except requests.exceptions.ConnectionError:
            logger.error("Error: Connot connect to the rubika server!")
            if retry_count < self.max_retries:
                sleep(self.retry_delay)
                return self._post(method, data, retry_count + 1)
            return None
            
        except Exception as e:
            logger.error(f"Unknown error: {e}")
            if retry_count < self.max_retries:
                sleep(self.retry_delay)
                return self._post(method, data, retry_count + 1)
            return None
    
    def _parse_text_metadata(self, text: str, parse_mode: str):
        formatter = GlyphWeaver()
        parsed = formatter.parse(text, parse_mode)
        return parsed.get("text"), parsed.get("metadata")
    
    def getUpdates(self, limit=100) -> dict:
        """دریافت آپدیت‌ها با مدیریت خطا"""
        data = {'limit': limit}
        
        if self.offset_id:
            data['offset_id'] = self.offset_id
        
        response = self._post("getUpdates", data)
        
        # اگر پاسخ معتبر نبود
        if not response:
            logger.warning("Invalid reponse of getUpdates method, try in 3 seconds...")
            sleep(3)
            return self.getUpdates(limit)
        
        # بررسی ساختار پاسخ
        if not isinstance(response, dict):
            logger.error(f"Invalid reponse of getUpdates method: {type(response)}")
            sleep(3)
            return self.getUpdates(limit)
        
        # بررسی وجود داده
        data = response.get('data', {})
        if not data:
            logger.warning("There is no data in response of getUpdates method!")
            sleep(1)
            return {}
        
        updates = data.get('updates', [])
        next_offset = data.get('next_offset_id')
        
        if next_offset:
            self.offset_id = next_offset
            db_tokenbots.set_key(self.token,next_offset)
            
        return updates
    
    def sendMessage(self, chat_id, text, reply_to_message_id=None,metadata=None):
        """ارسال پیام با مدیریت خطا"""
        data = {
            'chat_id': chat_id,
            'text': text,
        }
        if metadata:
            data["metadata"] = metadata
        else:
            text, metadata = self._parse_text_metadata(text,"Markdown")
            data["text"] = text
            if metadata:
                data["metadata"] = metadata
        
        if reply_to_message_id:
            data['reply_to_message_id'] = reply_to_message_id
        
        response = self._post("sendMessage", data)
        
        if not response:
            return self.sendMessage(chat_id, text, reply_to_message_id)
        return response
    
    def getChat(self, chat_id) -> ChatModel:
        data = {
            'chat_id': chat_id
        }
        
        response = self._post('getChat',data)
        print(response)
        if not response:
            return ChatModel({})
        
        return ChatModel(response.get('data').get('chat'))
    
    
    def getMessage(self,message_id):
        return db_message.get_key(message_id)
    
    
    def deleteMessage(self,chat_id,message_id):
        data = {
            'chat_id': chat_id,
            'message_id': message_id
        }
        
        response = self._post('deleteMessage',data)
        print(response)
    
    
    def _handle_start_update(self, update: dict):
        pass
        
    def _handle_stop_update(self, update: dict):
        pass
        
    def _handle_remove_message_update(self, update: dict):
        chat_id = update.get('chat_id')
        removed_message_id = update.get('removed_message_id')
        db_message.remove(chat_id+removed_message_id)
    
    def _handle_new_message_update(self, update: dict):
        for handler in self.handlers:
            if handler.type == UpdateTypeEnum.NewMessage.value:
                try:
                    message = update.get('new_message', {})
                    if not int(message.get('time', 0)) > self.time_run:
                        return
                    handler.handle(update, self)
                    message = update['new_message']
                    message_id = message.get('message_id',0)
                    chat_id = update['chat_id']
                    message['chat_id'] = chat_id
                    db_message.set_key(chat_id+message_id,message)
                    if chat_id.startswith('g') and chat_id not in self.groups:
                        self.groups.append(chat_id)
                        db_message.set_key("groups_fix",self.groups)
                except Exception as e:
                    logger.error(f"خطا در پردازش هندلر: {e}")
    
    def _handle_updated_message_update(self, update: dict):
        for handler in self.handlers:
            if handler.type == UpdateTypeEnum.UpdatedMessage.value:
                message = update.get('updated_message', {})
                if not int(message.get('time', 0)) > self.time_run:
                    return
                handler.handle(update, self)
                # message_id = message.get('message_id',0)
                # chat_id = update['chat_id']
                # message['chat_id'] = chat_id
                # db_message.set_key(chat_id+message_id,message)

    def _handle_updates(self, updates: list):
        if not updates:
            return
            
        for update in updates:
            update_type = update.get('type', None)
            try:
                if update_type == UpdateTypeEnum.StartedBot.value:
                    self._handle_start_update(update)
                elif update_type == UpdateTypeEnum.StoppedBot.value:
                    self._handle_stop_update(update)
                elif update_type == UpdateTypeEnum.RemovedMessage.value:
                    self._handle_remove_message_update(update)
                elif update_type == UpdateTypeEnum.NewMessage.value:
                    self._handle_new_message_update(update)
                elif update_type == UpdateTypeEnum.UpdatedMessage.value:
                    self._handle_updated_message_update(update)
            except Exception as e:
                logger.error(f"Error in handling update: {e}")
    
    def run(self):
        """اجرای بات با مدیریت خطا"""
        self.running = True
        logger.info("Robot Starting...!")
        
        while self.running:
            try:
                updates = self.getUpdates()
                
                if updates and isinstance(updates, list):
                    self._handle_updates(updates)
                
                sleep(0.5)
                
            except KeyboardInterrupt:
                logger.info("Robot Stopped By User.")
                self.running = False
                break
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                logger.info(f"try in {self.retry_delay} seconds...")
                sleep(self.retry_delay)
    
    def stop(self):
        """متوقف کردن بات"""
        self.running = False
        logger.info("Bot Stopped!")
