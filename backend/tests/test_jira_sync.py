import pytest
from unittest.mock import MagicMock, patch

from models.workspace_data import WorkspaceData
from models.workspace_integration import WorkspaceIntegrations
from services.sync.jira_sync import gather_and_store_jira_projects


def test_gather_and_store_jira_projects():
    db = MagicMock()

    integration = WorkspaceIntegrations(
        workspace_id=1,
        jira_base_url="https://test.atlassian.net",
        jira_admin_email="test@example.com",
        jira_api_key="encrypted-token",
    )

    db.query.return_value.filter.return_value.first.return_value = integration

    mock_projects = [
        {
            "id": "10001",
            "key": "PP",
            "name": "Project Pulse",
            "projectTypeKey": "software",
        },
        {
            "id": "10002",
            "key": "WEB",
            "name": "Website",
            "projectTypeKey": "business",
        },
    ]

    with patch("services.sync.jira_sync.JiraService") as mock_jira, \
         patch("services.sync.jira_sync.decrypt", return_value="token123") as mock_decrypt:

        mock_jira.return_value.fetch_projects.return_value = mock_projects

        count = gather_and_store_jira_projects(1, db)

    assert count == 2

    mock_decrypt.assert_called_once_with("encrypted-token")

    mock_jira.assert_called_once_with(
        "https://test.atlassian.net",
        "test@example.com",
        "token123",
    )

    assert db.add.call_count == 2
    assert db.flush.call_count == 2

    saved_project = db.add.call_args_list[0].args[0]

    assert isinstance(saved_project, WorkspaceData)
    assert saved_project.integration_id == 1
    assert saved_project.type == "project"
    assert saved_project.source == "jira"
    assert saved_project.title == "Project Pulse"

    assert saved_project.payload == {
        "id": "10001",
        "key": "PP",
        "name": "Project Pulse",
        "type": "software",
    }


def test_gather_and_store_jira_projects_no_api_key():
    db = MagicMock()

    integration = WorkspaceIntegrations(
        workspace_id=1,
        jira_base_url="https://test.atlassian.net",
        jira_admin_email="test@example.com",
        jira_api_key=None,
    )

    db.query.return_value.filter.return_value.first.return_value = integration

    with pytest.raises(ValueError, match="Jira API key not found"):
        gather_and_store_jira_projects(1, db)