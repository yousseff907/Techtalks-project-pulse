from unittest.mock import MagicMock

from app import app
from fastapi.testclient import TestClient
from utils.database import get_db
from utils.dependencies import get_current_user
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

	response = client.post("/workspaces", json={"name": "InvalidName_%00"})
	assert response.status_code == 400
	assert response.json()["detail"] == "Invalid name, contains dangerous characters"

def make_mock_user(user_id=1):
    user = MagicMock()
    user.id = user_id
    return user


def make_mock_workspace(workspace_id=10, name="Test Workspace", invite_code="ABC123"):
    workspace = MagicMock()
    workspace.id = workspace_id
    workspace.name = name
    workspace.invite_code = invite_code
    return workspace


def make_mock_db(workspace=None, existing_member=None, workspace_count=0):
    mock_db = MagicMock()
    def query_side_effect(model):
        mock_query = MagicMock()
        if model == Workspace:
            mock_query.filter.return_value.first.return_value = workspace
        elif model == WorkspaceMember:
            mock_query.filter.return_value.first.return_value = existing_member
            mock_query.filter.return_value.count.return_value = workspace_count
        return mock_query

    mock_db.query.side_effect = query_side_effect
    return mock_db


def override_dependencies(mock_user, mock_db):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db


def clear_dependencies():
    app.dependency_overrides.clear()


def test_join_workspace_success():
    mock_user = make_mock_user(user_id=1)
    mock_workspace = make_mock_workspace(workspace_id=10, name="Test Workspace")
    mock_db = make_mock_db(workspace=mock_workspace, existing_member=None, workspace_count=2)
    override_dependencies(mock_user, mock_db)

    response = client.post("/workspaces/join", json={"invite_code": "ABC123"})

    assert response.status_code == 200
    assert response.json() == {"workspace_id": 10, "name": "Test Workspace"}
    clear_dependencies()


def test_join_workspace_dangerous_invite_code():
    mock_user = make_mock_user()
    mock_db = make_mock_db()
    override_dependencies(mock_user, mock_db)

    response = client.post("/workspaces/join", json={"invite_code": "<script>"})

    assert response.status_code == 400
    clear_dependencies()


def test_join_workspace_invalid_invite_code():
    mock_user = make_mock_user()
    mock_db = make_mock_db(workspace=None)
    override_dependencies(mock_user, mock_db)

    response = client.post("/workspaces/join", json={"invite_code": "INVALID"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Invalid invite code"
    clear_dependencies()


def test_join_workspace_already_a_member():
    mock_user = make_mock_user(user_id=1)
    mock_workspace = make_mock_workspace(workspace_id=10)
    mock_existing_member = MagicMock()
    mock_db = make_mock_db(workspace=mock_workspace, existing_member=mock_existing_member)
    override_dependencies(mock_user, mock_db)

    response = client.post("/workspaces/join", json={"invite_code": "ABC123"})

    assert response.status_code == 409
    assert response.json()["detail"] == "You are already a member of this workspace"
    clear_dependencies()


def test_join_workspace_exceeds_limit():
    mock_user = make_mock_user(user_id=1)
    mock_workspace = make_mock_workspace(workspace_id=10)
    mock_db = make_mock_db(workspace=mock_workspace, existing_member=None, workspace_count=5)
    override_dependencies(mock_user, mock_db)

    response = client.post("/workspaces/join", json={"invite_code": "ABC123"})

    assert response.status_code == 400
    assert response.json()["detail"] == "You have reached the maximum number of workspaces (5)"
    clear_dependencies()


def test_join_workspace_at_exactly_limit_boundary():
    mock_user = make_mock_user(user_id=1)
    mock_workspace = make_mock_workspace(workspace_id=10)
    mock_db = make_mock_db(workspace=mock_workspace, existing_member=None, workspace_count=4)
    override_dependencies(mock_user, mock_db)

    response = client.post("/workspaces/join", json={"invite_code": "ABC123"})

    assert response.status_code == 200
    clear_dependencies()


def test_join_workspace_new_member_row_is_created():
    mock_user = make_mock_user(user_id=1)
    mock_workspace = make_mock_workspace(workspace_id=10)
    mock_db = make_mock_db(workspace=mock_workspace, existing_member=None, workspace_count=0)
    override_dependencies(mock_user, mock_db)

    client.post("/workspaces/join", json={"invite_code": "ABC123"})

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

    added_member = mock_db.add.call_args[0][0]
    assert added_member.user_id == 1
    assert added_member.workspace_id == 10
    assert added_member.role == "member"
    clear_dependencies()