import requests
import time
import logging
from typing import Optional, Dict, Any, Union
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DarametAPI:
    BASE_URL = "https://daramet.com"

    def __init__(
        self,
        username: str,
        token: str,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        status_forcelist: tuple = (429, 500, 502, 503, 504),
        timeout: int = 30,
    ):
        self.username = username
        self.token = token
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.status_forcelist = status_forcelist
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": token,
            "Content-Type": "application/json"
        })

        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _request(self, method: str, path: str, retry_count: int = 0, **kwargs) -> Dict[str, Any]:
        url = self.BASE_URL + path
        kwargs.setdefault("timeout", self.timeout)
        
        logger.info(f"POST Request: {url}")

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout as e:
            logger.warning(f"Timeout on request to {url} (attempt {retry_count + 1}/{self.max_retries})")
            return self._retry_or_raise(method, path, retry_count, e, **kwargs)

        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error to {url} (attempt {retry_count + 1}/{self.max_retries})")
            return self._retry_or_raise(method, path, retry_count, e, **kwargs)

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            if status_code in self.status_forcelist:
                logger.warning(f"Status {status_code} on {url} (attempt {retry_count + 1}/{self.max_retries})")
                return self._retry_or_raise(method, path, retry_count, e, **kwargs)
            logger.error(f"HTTP error {status_code} on {url}: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error on {url}: {e}")
            raise

    def _retry_or_raise(self, method: str, path: str, retry_count: int, exception: Exception, **kwargs) -> Dict[str, Any]:
        if retry_count >= self.max_retries - 1:
            logger.error(f"All retry attempts for {path} failed: {exception}")
            raise exception

        sleep_time = self.backoff_factor * (2 ** retry_count)
        logger.info(f"Waiting {sleep_time:.2f} seconds before retry...")
        time.sleep(sleep_time)

        return self._request(method, path, retry_count + 1, **kwargs)

    def get_all_donates(self, page: int = 1) -> Dict[str, Any]:
        return self._request("POST", "/api/v2/Donates/All", json={"page": page})

    def get_recent_messages(self, page: int = 1) -> Dict[str, Any]:
        return self._request("POST", "/api/v2/Donates/Messages", json={"Page": page})

    def get_last_messages_with_message(self) -> Dict[str, Any]:
        return self._request("GET", "/api/Donates/Messages")

    def search_donates(self, term: Union[str, int]) -> Dict[str, Any]:
        return self._request("POST", "/api/v2/Donates/Search", json={"term": term})

    def get_high_to_low(self) -> Dict[str, Any]:
        return self._request("GET", "/api/Donates/HighToLow")

    def get_goal(self) -> Dict[str, Any]:
        return self._request("GET", "/api/v2/Goal")

    def get_total(self) -> Dict[str, Any]:
        return self._request("GET", "/api/v2/Total")

    def build_webintent_url(self, donate_amount: int, message: Optional[str] = None) -> str:
        params = {"webintent": "", "donate": str(donate_amount)}
        if message:
            params["message"] = message
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.BASE_URL}/{self.username}?{query}"