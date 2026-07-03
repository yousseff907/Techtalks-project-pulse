from unittest.mock import MagicMock, patch
from services.jira_service import JiraService


def test_fetch_users_pagination():
    service = JiraService("https://fake-jira.com", "email", "token")

    page1 = MagicMock()
    page1.json.return_value = {
        "values": [
            {"accountId": "1", "displayName": "A", "emailAddress": "a@test.com"},
            {"accountId": "2", "displayName": "B", "emailAddress": "b@test.com"},
        ]
    }
    page1.raise_for_status = MagicMock()

    page2 = MagicMock()
    page2.json.return_value = {
        "values": [
            {"accountId": "3", "displayName": "C", "emailAddress": "c@test.com"}
        ]
    }
    page2.raise_for_status = MagicMock()

    with patch("services.jira_service.requests.Session.get", side_effect=[page1, page2]):
        users = service.fetch_users()

    assert len(users) == 3
    assert users[0]["id"] == "1"
    assert users[2]["id"] == "3"
