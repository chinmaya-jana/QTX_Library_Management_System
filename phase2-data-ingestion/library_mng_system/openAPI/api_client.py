
import time
import requests
from logs import logger


class OpenLibraryAPIClient:
    BASE_URL = "https://openlibrary.org"
    RATE_LIMIT_SECONDS = 1  # 1 request per second

    def __init__(self):
        self.last_request_time = 0

    def _get(self, endpoint: str, params: dict = None) -> dict:
        full_url = f"{self.BASE_URL}{endpoint}"
        self._respect_rate_limit()

        try:
            response = requests.get(full_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.warning(f"API request failed: {e}")
            return {}

    def _respect_rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_SECONDS:
            time.sleep(self.RATE_LIMIT_SECONDS - elapsed)
        self.last_request_time = time.time()

    def search_author(self, author_name: str) -> dict:
        return self._get("/search/authors.json", params={"q": author_name})

    def get_author_works(self, author_key: str, limit: int = 20) -> dict:
        return self._get(f"/authors/{author_key}/works.json", params={"limit": limit})

    def get_work_details(self, work_key: str) -> dict:
        return self._get(f"/works/{work_key}.json")
