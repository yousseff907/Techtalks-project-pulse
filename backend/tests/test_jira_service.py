from unittest.mock import Mock, patch
from services.jira_service import JiraService


def test_fetch_users_pagination():
    first_response = Mock()
    first_response.raise_for_status.return_value = None
    first_response.json.return_value = [
        {"accountId": "1", "displayName": "User 1"},
        {"accountId": "2", "displayName": "User 2"},
    ]

    second_response = Mock()
    second_response.raise_for_status.return_value = None
    second_response.json.return_value = [
        {"accountId": "3", "displayName": "User 3"},
    ]

    with patch(
        "services.jira_service.requests.get",
        side_effect=[first_response, second_response],
    ) as mock_get:
        service = JiraService(
            "https://example.atlassian.net",
            "email",
            "token",
        )

        users = service.fetch_users(
            start_at=0,
            max_results=2,
        )

        assert len(users) == 3
        assert users[0]["accountId"] == "1"
        assert users[1]["accountId"] == "2"
        assert users[2]["accountId"] == "3"
        assert mock_get.call_count == 2

def test_fetch_users_no_users():
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = []

    with patch(
        "services.jira_service.requests.get",
        return_value=response,
    ):
        service = JiraService(
            "https://example.atlassian.net",
            "email",
            "token",
        )

        users = service.fetch_users()

        assert users == []