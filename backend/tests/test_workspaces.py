from app import app
from fastapi.testclient import TestClient
from models.user import User
from models.workspace import Workspace
from models.workspace_member import WorkspaceMember

client = TestClient(app)

def	test_workspace_creation(db_session, mock_user):
	user = User(username="test_user", email="test_user@example.com", is_verified=True)
	db_session.add(user)
	db_session.flush()

	mock_user.id = user.id

	response = client.post("/workspaces", json={"name": "ValidName"})
	assert response.status_code == 201
	assert response.json()["workspace_id"]
	assert response.json()["name"]
	assert response.json()["invite_code"]
	assert response.json()["invite_link"]
	
	workspace = db_session.query(Workspace).filter(Workspace.id == response.json()["workspace_id"]).first()
	assert workspace is not None
	assert workspace.integration is not None
	
	workspace_member = db_session.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == response.json()["workspace_id"], WorkspaceMember.user_id == mock_user.id).first()
	assert workspace_member is not None
	assert workspace_member.role == "owner"

	for i in range(4):
		client.post("/workspaces", json={"name": f"ValidName{i}"})

	response = client.post("/workspaces", json={"name": "ValidName_6"})
	assert response.status_code == 400
	assert response.json()["detail"] == "You have reached the maximum number of workspaces (5)"

	response = client.post("/workspaces", json={"name": f"InvalidName_%00"})
	assert response.status_code == 400
	assert response.json()["detail"] == "Invalid name, contains dangerous characters"