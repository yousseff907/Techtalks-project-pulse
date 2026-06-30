from unittest.mock import patch
from fastapi.testclient import TestClient
from app import app
from models.user import User
from models.workspace import Workspace
from models.workspace_integration import WorkspaceIntegrations

client = TestClient(app)

@patch("routes.integrations.is_valid_notion_credentials")
def	test_successfull_notion_integration_existing_integration(mock_is_valid_credentials, db_session, mock_user):
	mock_user.id = 1
	first_correct_workspace = Workspace(name="first_correct_workspace", created_by=mock_user.id, invite_code="xxx", invite_link="xxx.example")
	db_session.add(first_correct_workspace)
	db_session.flush()
	first_correct_workspace.integration = WorkspaceIntegrations(workspace_id=first_correct_workspace.id)
	db_session.add(first_correct_workspace.integration)
	db_session.flush()

	mock_is_valid_credentials.return_value = True
	response = client.patch(f"/workspaces/{first_correct_workspace.id}/integrations/notion", json={"api_key": "correct_key"})

	assert response.status_code == 200
	assert response.json()["message"] == "Notion credentials saved successfully"

	db_session.refresh(first_correct_workspace.integration)
	assert first_correct_workspace.integration.notion_api_key is not None
	assert first_correct_workspace.integration.notion_connected_at is not None

@patch("routes.integrations.is_valid_notion_credentials")
def	test_successfull_notion_integration_non_existing_integration(mock_is_valid_credentials, db_session, mock_user):
	mock_user.id = 2
	second_correct_workspace = Workspace(name="second_correct_workspace", created_by=mock_user.id, invite_code="yyy", invite_link="yyy.example")
	db_session.add(second_correct_workspace)
	db_session.flush()

	mock_is_valid_credentials.return_value = True
	response = client.patch(f"/workspaces/{second_correct_workspace.id}/integrations/notion", json={"api_key": "correct_key"})

	assert response.status_code == 200
	assert response.json()["message"] == "Notion credentials saved successfully"
	
	db_session.refresh(second_correct_workspace.integration)
	assert second_correct_workspace.integration.notion_api_key is not None
	assert second_correct_workspace.integration.notion_connected_at is not None

def	test_failed_notion_integration_non_existing_workspace(db_session, mock_user):
	response = client.patch("/workspaces/{0}/integrations/notion", json={"api_key": "N/A"})
	assert response.status_code == 404
	assert response.json()["detail"] == "Workspace not found"

def	test_failed_notion_integration_not_workspace_creator(db_session, mock_user):
	mock_user.id = 1
	first_correct_workspace = Workspace(name="first_correct_workspace", created_by=2, invite_code="xxx", invite_link="xxx.example")
	db_session.add(first_correct_workspace)
	db_session.flush()
	first_correct_workspace.integration = WorkspaceIntegrations(workspace_id=first_correct_workspace.id)
	db_session.add(first_correct_workspace.integration)
	db_session.flush()

	response = client.patch(f"/workspaces/{first_correct_workspace.id}/integrations/notion", json={"api_key": "correct_key"})
	
	assert response.status_code == 403
	assert response.json()["detail"] == "Only the workspace owner can configure integrations"

@patch("routes.integrations.is_valid_notion_credentials")
def test_failed_notion_integration_invalid_credentials(mock_is_valid_credentials, db_session, mock_user):
	mock_user.id = 1
	workspace = Workspace(name="workspace", created_by=mock_user.id, invite_code="xxx", invite_link="xxx.example")
	db_session.add(workspace)
	db_session.flush()

	mock_is_valid_credentials.return_value = False
	response = client.patch(f"/workspaces/{workspace.id}/integrations/notion", json={"api_key": "invalid_key"})

	assert response.status_code == 400
	assert response.json()["detail"] == "Invalid Notion credentials"

def test_failed_notion_integration_dangerous_input(db_session, mock_user):
	mock_user.id = 1
	workspace = Workspace(name="workspace", created_by=mock_user.id, invite_code="xxx", invite_link="xxx.example")
	db_session.add(workspace)
	db_session.flush()

	response = client.patch(f"/workspaces/{workspace.id}/integrations/notion", json={"api_key": "<script>alert(1)</script>"})

	assert response.status_code == 400
	assert response.json()["detail"] == "Invalid Notion credentials, contains dangerous characters"