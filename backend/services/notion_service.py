from fastapi import params
import requests


class NotionService:
    def __init__(self, api_token):
        self.api_token = api_token
        self.base_url = "https://api.notion.com/v1"

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Notion-Version": "2022-06-28",
        }

    def fetch_users(self):
        params = {}
        users = []

        while True:
            response = requests.get(
                f"{self.base_url}/users",
                headers=self._headers(),
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            for u in data.get("results", []):
                users.append({
                    "id": u.get("id", ""),
                    "name": u.get("name", ""),
                    "email": u.get("person", {}).get("email", ""),
                    "active": bool(u.get("is_active", False)),
                })

            if data.get("has_more"):
                params["start_cursor"] = data.get("next_cursor")
            else:
                break

        return users

    def fetch_databases(self):
        url = f"{self.base_url}/search"
        body = {
            "filter": {
                "value": "database",
                "property": "object",
            }
        }

        databases = []

        while True:
            response = requests.post(url, headers=self._headers(), json=body)
            response.raise_for_status()
            data = response.json()

            for db in data.get("results", []):
                title_array = db.get("title", [])
                title = title_array[0].get("plain_text", "") if title_array else ""

                databases.append({
                    "id": db.get("id", ""),
                    "title": title,
                })

            if data.get("has_more"):
                body["start_cursor"] = data.get("next_cursor")
            else:
                break

        return databases