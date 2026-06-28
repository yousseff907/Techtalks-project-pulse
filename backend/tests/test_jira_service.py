from unittest.mock import MagicMock, patch, Mock
from services.jira_service import JiraService


@patch("services.jira_service.requests.get")
def test_fetch_users(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = [
        {
            "accountId": "123",
            "displayName": "John Doe",
            "emailAddress": "john@test.com",
            "active": True,
        },
        {
            "accountId": "456",
            "displayName": "Jane Smith",
            # email missing
            "active": False,
        },
    ]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    service = JiraService("url", "email", "token")
    result = service.fetch_users()

    assert result[0] == {
        "id": "123",
        "name": "John Doe",
        "email": "john@test.com",
        "active": True,
    }
    assert result[1] == {
        "id": "456",
        "name": "Jane Smith",
        "email": "",
        "active": False,
    }
def test_fetch_projects(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "values": [{"id": "1", "key": "PROJ1"}],
            "isLast": True
        }
        mock_response.raise_for_status = MagicMock()
        self.service.session.get.return_value = mock_response
        projects = self.service.fetch_projects()
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["key"], "PROJ1")