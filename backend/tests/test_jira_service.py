import unittest
from unittest.mock import MagicMock
from services.jira_service import JiraService

class TestJiraService(unittest.TestCase):
    def setUp(self):
        self.service = JiraService("https://fake-jira.com", "email", "token")
        self.service.session = MagicMock()

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

if __name__ == "__main__":
    unittest.main()