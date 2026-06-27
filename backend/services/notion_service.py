import requests


class NotionService:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Accept": "application/json",
        }

    def fetch_users(self):
        response = requests.get(
            f"{self.base_url}/users",
            headers=self.headers,
        )
        response.raise_for_status()
        users = response.json().get("results", [])

        return [
            {
                "id": u.get("id", ""),
                "name": u.get("name", ""),
                "type": u.get("type", ""),
                "avatar_url": u.get("avatar_url", ""),
            }
            for u in users
        ]