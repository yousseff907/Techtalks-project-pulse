import requests


class JiraService:
    def __init__(self, base_url, email, api_token):
        self.base_url = base_url
        self.auth = (email, api_token)

    def fetch_users(self, start_at=0, max_results=50):
        response = requests.get(
            f"{self.base_url}/rest/api/3/user/search",
            auth=self.auth,
            headers={"Accept": "application/json"},
            params={
                "startAt": start_at,
                "maxResults": max_results
            },
        )

        response.raise_for_status()
        users = response.json()

        # API returns a plain list
        return [
            {
                "id": u.get("accountId", ""),
                "name": u.get("displayName", ""),
                "email": u.get("emailAddress", ""),
            }
            for u in users
        ]

    def fetch_projects(self, start_at=0, max_results=50):
        all_projects = []

        while True:
            response = requests.get(
                f"{self.base_url}/rest/api/3/project/search",
                auth=self.auth,
                headers={"Accept": "application/json"},
                params={
                    "startAt": start_at,
                    "maxResults": max_results
                },
            )

            response.raise_for_status()
            data = response.json()

            projects = data.get("values", [])
            all_projects.extend(projects)

            if data.get("isLast", True):
                break

            start_at += max_results

        return all_projects
