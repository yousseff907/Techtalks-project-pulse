from requests import get


def is_valid_notion_credentials(base_url: str, token: str) -> bool:
    response = get(
        f"{base_url}/users/me",
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Accept": "application/json",
        },
    )

    if response.status_code != 200:
        return False

    return True