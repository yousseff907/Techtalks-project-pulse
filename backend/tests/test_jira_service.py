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

    def test_fetch_users_pagination(self):
        # Page 1
        page1 = MagicMock()
        page1.json.return_value = [
            {"accountId": "1", "displayName": "A", "emailAddress": "a@test.com", "active": True},
            {"accountId": "2", "displayName": "B", "emailAddress": "b@test.com", "active": True},
        ]
        page1.raise_for_status = MagicMock()

        # Page 2
        page2 = MagicMock()
        page2.json.return_value = [
            {"accountId": "3", "displayName": "C", "emailAddress": "c@test.com", "active": True}
        ]
        page2.raise_for_status = MagicMock()

        self.service.session.get.side_effect = [page1, page2]

        users = self.service.fetch_users()

        self.assertEqual(len(users), 3)
        self.assertEqual(users[0]["id"], "1")
        self.assertEqual(users[2]["id"], "3")


if __name__ == "__main__":
    unittest.main()