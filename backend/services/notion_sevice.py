import requests


class NotionService:
    def __init__(self, token):
        self.base_url = "https://api.notion.com/v1"
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
                "email": (
                    u.get("person", {}).get("email", "")
                    if isinstance(u.get("person"), dict)
                    else ""
                ),
            }
            for u in users
        ]