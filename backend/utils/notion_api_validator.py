from requests import get


def is_valid_notion_credentials(api_key: str) -> bool:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",  #Taken from Notion API on Notion
    }
    response = get("https://api.notion.com/v1/users/me", headers=headers)
    if response.status_code != 200:
        return False
    return True