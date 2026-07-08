from unittest.mock import Mock, patch
from services.jira_service import JiraService


def test_fetch_issues_pagination():
    first_response = Mock()
    first_response.raise_for_status.return_value = None
    first_response.json.return_value = {
        "issues": [{"id": "1"}, {"id": "2"}],
    }

    second_response = Mock()
    second_response.raise_for_status.return_value = None
    second_response.json.return_value = {
        "issues": [{"id": "3"}],
    }

    with patch(
        "services.jira_service.requests.get",
        side_effect=[first_response, second_response],
    ) as mock_get:
        service = JiraService(
            "https://example.atlassian.net",
            "email",
            "token",
        )

        issues = service.fetch_issues(
            start_at=0,
            max_results=2,
            jql="project = TEST",
        )

        assert len(issues) == 3
        assert issues[0]["id"] == "1"
        assert issues[1]["id"] == "2"
        assert issues[2]["id"] == "3"

        assert mock_get.call_count == 2

        assert mock_get.call_args_list[0].kwargs["params"] == {
            "startAt": 0,
            "maxResults": 2,
            "jql": "project = TEST",
        }