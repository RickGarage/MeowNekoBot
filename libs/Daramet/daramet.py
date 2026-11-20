import threading
import time
from typing import Callable, Optional
from .daramet_api import DarametAPI

class Donate:
    def __init__(self, data: dict):
        inner = data['donator_data']
        self.donator = data.get('donator', '')
        self.id = inner.get('id', 0)
        self.message = inner.get('message', '')
        self.amount = inner.get('amount', 0)
        self.timestamp = inner.get('timestamp', 0)
        

class Daramet:
    def __init__(self, username: str, token: str, handler: Callable[[Donate], None], seconds_ago: int = 10):
        self.daramet = DarametAPI(username, token)
        self.handler = handler
        self.seconds_ago = seconds_ago
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_checked_timestamp = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def get_new_timestamp(self) -> int:
        return int(time.time())
    
    def handle_donate(self,donate: Donate):
        
        donate_timestamp = donate.timestamp
        
        if self._last_checked_timestamp == donate_timestamp:
            return
        self._last_checked_timestamp = donate_timestamp
        
        timestamp = donate_timestamp - self.get_new_timestamp()
        timestamp = timestamp-timestamp-timestamp
        
        if (timestamp - self.seconds_ago) > self.seconds_ago:
            return
        
        func = self.handler
        func(donate)
        
    
    def handle_donates(self,donates:list):
        a = len(donates)
        self.handle_donate(Donate(donates[a-a-a]))

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                response = self.daramet.get_all_donates()

                if isinstance(response, list):
                    donates_data = response
                else:
                    donates_data = []

                if donates_data:
                    self.handle_donates(donates_data)

            except Exception as e:
                print(f"Error in get donates: {e}")

            self._stop_event.wait(timeout=1)
    
        
