from unittest.mock import MagicMock, patch

from models.workspace_data import WorkspaceData
from models.workspace_integration import WorkspaceIntegrations
from services.sync.jira_sync import gather_and_store_jira_tasks


def test_gather_and_store_jira_tasks():

    db = MagicMock()

    integration = WorkspaceIntegrations(
        workspace_id=1,
        jira_base_url="https://test.atlassian.net",
        jira_admin_email="test@example.com",
        jira_api_key="encrypted-token",
    )

    db.query.return_value.filter.return_value.first.return_value = integration

    mock_issues = [
        {
            "id": "10001",
            "key": "PP-1",
            "fields": {
                "summary": "Create dashboard",
                "description": "Build project dashboard",
                "status": {
                    "name": "In Progress"
                },
                "priority": {
                    "name": "High"
                },
                "assignee": {
                    "displayName": "John"
                },
                "reporter": {
                    "displayName": "Jane"
                },
                "project": {
                    "key": "PP"
                },
                "created": "2026-07-10T10:00:00.000Z",
                "updated": "2026-07-11T10:00:00.000Z",
                "due_date": "2026-07-20T00:00:00",
            },
        }
    ]

    with patch(
        "services.sync.jira_sync.JiraService"
    ) as mock_jira, patch(
        "services.sync.jira_sync.decrypt",
        return_value="token123"
    ):

        mock_jira.return_value.fetch_issues.return_value = mock_issues

        count = gather_and_store_jira_tasks(1, db)

    assert count == 1

    mock_jira.assert_called_once_with(
        "https://test.atlassian.net",
        "test@example.com",
        "token123",
    )

    assert db.add.call_count == 1
    assert db.flush.call_count == 1

    saved_task = db.add.call_args_list[0].args[0]

    assert isinstance(saved_task, WorkspaceData)
    assert saved_task.type == "task"
    assert saved_task.source == "jira"
    assert saved_task.title == "Create dashboard"
    assert saved_task.status == "IN_PROGRESS"

    assert saved_task.payload == {
        "id": "10001",
        "key": "PP-1",
        "title": "Create dashboard",
        "description": "Build project dashboard",
        "status": "IN_PROGRESS",
        "priority": "High",
        "assignee": "John",
        "reporter": "Jane",
        "project": "PP",
        "created_at": "2026-07-10T10:00:00+00:00",
        "updated_at": "2026-07-11T10:00:00+00:00",
        "due_date": "2026-07-20",
    }