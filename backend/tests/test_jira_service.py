from unittest.mock import MagicMock, patch
from services.jira_service import JiraService


def test_fetch_projects():
    service = JiraService("https://fake-jira.com", "email", "token")

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "values": [{"id": "1", "key": "PROJ1"}],
        "isLast": True
    }
    mock_response.raise_for_status = MagicMock()

    with patch("services.jira_service.requests.get") as mock_get:
        mock_get.return_value = mock_response

        projects = service.fetch_projects()

        assert len(projects) == 1
        assert projects[0]["key"] == "PROJ1"
