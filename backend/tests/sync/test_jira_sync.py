from unittest.mock import MagicMock, patch
from models.workspace_data import WorkspaceData
from models.workspace_integration import WorkspaceIntegrations
from services.sync.jira_sync import gather_and_store_jira_users


def test_gather_and_store_jira_users():
    db = MagicMock()

    # Mock Jira integration
    integration = WorkspaceIntegrations(
        id=1,
        base_url="https://test.atlassian.net",
        email="test@example.com",
        api_token="token123",
    )

    db.query.return_value.filter.return_value.first.return_value = integration

    # Mock Jira API response
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

    with patch(
        "app.services.sync.jira_sync.JiraService"
    ) as mock_jira_service:

        mock_jira_service.return_value.fetch_users.return_value = mock_users

        count = gather_and_store_jira_users(1, db)

    # Check count
    assert count == 2

    # Check JiraService was created correctly
    mock_jira_service.assert_called_once_with(
        base_url="https://test.atlassian.net",
        email="test@example.com",
        api_token="token123",
    )

    # Check db.add called twice
    assert db.add.call_count == 2

    # Check stored payloads
    first_saved = db.add.call_args_list[0].args[0]

    assert isinstance(first_saved, WorkspaceData)
    assert first_saved.integration_id == 1
    assert first_saved.type == "user"
    assert first_saved.source == "jira"

    assert first_saved.payload == {
        "id": "abc123",
        "name": "John Doe",
        "email": "john@example.com",
        "active": True,
    }

    # flush called for each inserted row
    assert db.flush.call_count == 2