import pytest
from unittest.mock import patch

from models.workspace_data import WorkspaceData
from models.workspace_integration import WorkspaceIntegrations
from services.sync.jira_sync import (
    gather_and_store_jira_users,
    gather_and_store_jira_projects,
)


def test_gather_and_store_jira_users(mock_db):

    integration = WorkspaceIntegrations(
        workspace_id=1,
        jira_base_url="https://test.atlassian.net",
        jira_admin_email="test@example.com",
        jira_api_key="encrypted-token",
    )

    mock_db.query.return_value.filter.return_value.first.return_value = integration

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

    with patch("services.sync.jira_sync.JiraService") as mock_jira, \
         patch("services.sync.jira_sync.decrypt", return_value="token123") as mock_decrypt:

        mock_jira.return_value.fetch_users.return_value = mock_users

        count = gather_and_store_jira_users(1, mock_db)

    assert count == 2

    mock_decrypt.assert_called_once_with("encrypted-token")

    mock_jira.assert_called_once_with(
        "https://test.atlassian.net",
        "test@example.com",
        "token123",
    )

    assert mock_db.add.call_count == 2
    assert mock_db.flush.call_count == 1

    saved_user = mock_db.add.call_args_list[0].args[0]

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


def test_gather_and_store_jira_users_no_api_key(mock_db):

    integration = WorkspaceIntegrations(
        workspace_id=1,
        jira_base_url="https://test.atlassian.net",
        jira_admin_email="test@example.com",
        jira_api_key=None,
    )

    mock_db.query.return_value.filter.return_value.first.return_value = integration

    with pytest.raises(ValueError, match="Jira API key not found"):
        gather_and_store_jira_users(1, mock_db)


def test_gather_and_store_jira_projects(mock_db):

    integration = WorkspaceIntegrations(
        workspace_id=1,
        jira_base_url="https://test.atlassian.net",
        jira_admin_email="test@example.com",
        jira_api_key="encrypted-token",
    )

    mock_db.query.return_value.filter.return_value.first.return_value = integration

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

        count = gather_and_store_jira_projects(1, mock_db)

    assert count == 2

    mock_decrypt.assert_called_once_with("encrypted-token")

    mock_jira.assert_called_once_with(
        "https://test.atlassian.net",
        "test@example.com",
        "token123",
    )

    assert mock_db.add.call_count == 2
    assert mock_db.flush.call_count == 1

    saved_project = mock_db.add.call_args_list[0].args[0]

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


def test_gather_and_store_jira_projects_no_api_key(mock_db):

    integration = WorkspaceIntegrations(
        workspace_id=1,
        jira_base_url="https://test.atlassian.net",
        jira_admin_email="test@example.com",
        jira_api_key=None,
    )

    mock_db.query.return_value.filter.return_value.first.return_value = integration

    with pytest.raises(ValueError, match="Jira API key not found"):
        gather_and_store_jira_projects(1, mock_db)