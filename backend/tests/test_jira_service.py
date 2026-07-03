import unittest
from unittest.mock import MagicMock, patch
from services.jira_service import JiraService


class TestJiraService(unittest.TestCase):
    def setUp(self):
        self.service = JiraService("https://fake-jira.com", "email", "token")

    @patch("services.jira_service.requests.get")
    def test_fetch_projects(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "values": [{"id": "1", "key": "PROJ1"}],
            "isLast": True
        }
        mock_response.raise_for_status = MagicMock()

        mock_get.return_value = mock_response

        projects = self.service.fetch_projects()

        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["key"], "PROJ1")


if __name__ == "__main__":
    unittest.main()
