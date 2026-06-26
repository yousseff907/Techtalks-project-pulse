import requests


class JiraService:
    def __init__(self, base_url, email, api_token):
        self.base_url = base_url
        self.auth = (email, api_token)

    def fetch_users(self):
        response = requests.get(
            f"{self.base_url}/rest/api/3/user/search",
            auth=self.auth,
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        users = response.json()

        return [
            {
                "id": u.get("accountId", ""),
                "name": u.get("displayName", ""),
                "email": u.get("emailAddress", ""),
                "active": bool(u.get("active", False)),
            }
            for u in users
        ]
