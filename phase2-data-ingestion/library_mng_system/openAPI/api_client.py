import time
import requests

BASE_URL = "https://openlibrary.org"

class OpenLibraryClient:
    def __init__(self):
        self.session = requests.Session()

    def search_author(self, author_name: str):
        url = f"{BASE_URL}/search/authors.json?q={author_name}"
        response = self.session.get(url)
        time.sleep(1)
        if response.status_code == 200:
            data = response.json()
            if data.get("docs"):
                return data["docs"][0]  # Return best match
        return None

    def get_author_details(self, author_key: str):
        url = f"{BASE_URL}/authors/{author_key}.json"
        response = self.session.get(url)
        time.sleep(1)
        if response.status_code == 200:
            return response.json()
        return {}

    def get_author_works(self, author_key: str, limit: int):
        url = f"{BASE_URL}/authors/{author_key}/works.json?limit={limit}"
        response = self.session.get(url)
        time.sleep(1)
        if response.status_code == 200:
            return response.json().get("entries", [])
        return []

    def get_work_details(self, work_key: str):
        url = f"{BASE_URL}/works/{work_key}.json"
        response = self.session.get(url)
        time.sleep(1)
        if response.status_code == 200:
            return response.json()
        return None

    def get_editions_for_work(self, work_key: str):
        url = f"{BASE_URL}/works/{work_key}/editions.json?limit=5" # I set it as a limit 5
        response = self.session.get(url)
        time.sleep(1)
        if response.status_code == 200:
            return response.json()
        return {}
