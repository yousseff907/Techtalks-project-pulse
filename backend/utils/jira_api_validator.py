from requests import get

def is_valid_jira_credentials(base_url: str, email: str, api_key: str) -> bool:
	response = get(f"{base_url}/rest/api/3/myself", auth=(email, api_key), headers={"Accept": "application/json"})
	if response.status_code != 200:
		return False
	return True