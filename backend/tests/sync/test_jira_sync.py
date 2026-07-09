from unittest.mock import MagicMock, patch

from models.workspace_data import WorkspaceData
from models.workspace_integration import WorkspaceIntegrations
from services.sync.jira_sync import gather_and_store_jira_users


def test_gather_and_store_jira_users():
    db = MagicMock()

    integration = WorkspaceIntegrations(
        workspace_id=1,
        jira_base_url="https://test.atlassian.net",
        jira_admin_email="test@example.com",
        jira_api_key="token123",
    )

    db.query.return_value.filter.return_value.first.return_value = integration

    mock_users = [
        {
            "accountId": "abc123",
            "displayName": "John Doe",
            "emailAddress": "john@example.com",
            "active": True,
        },
        {
            "accountId": "xyz456",
            "displayName": "Jane Smith",
            "emailAddress": "jane@example.com",
            "active": False,
        },
    ]

    with patch("services.sync.jira_sync.JiraService") as mock_jira:
        mock_jira.return_value.fetch_users.return_value = mock_users

        count = gather_and_store_jira_users(1, db)

    assert count == 2

    mock_jira.assert_called_once_with(
        "https://test.atlassian.net",
        "test@example.com",
        "token123",
    )

    assert db.add.call_count == 2
    assert db.flush.call_count == 1

    saved_user = db.add.call_args_list[0].args[0]

    assert isinstance(saved_user, WorkspaceData)
    assert saved_user.integration_id == 1
    assert saved_user.type == "user"
    assert saved_user.source == "jira"

    assert saved_user.payload == {
        "id": "abc123",
        "name": "John Doe",
        "email": "john@example.com",
        "active": True,
    }