from unittest.mock import MagicMock, patch

from sqlalchemy.exc import IntegrityError

from app import app
from fastapi.testclient import TestClient
from utils.database import get_db
from utils.dependencies import get_current_user
from models.user import User
from models.workspace import Workspace
from models.workspace_member import WorkspaceMember
from models.workspace_integration import WorkspaceIntegrations
from models.workspace_data import WorkspaceData

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

#Leave workspace tests

def test_leave_workspace_as_member_success(db_session, mock_user):
    owner = User(username="ws_owner", email="owner@example.com", is_verified=True)
    member_user = User(username="ws_member", email="member@example.com", is_verified=True)
    db_session.add(owner)
    db_session.add(member_user)
    db_session.flush()
    
    workspace = Workspace(name="Leave Workspace", created_by=owner.id, invite_code="leave1", invite_link="link1")
    db_session.add(workspace)
    db_session.flush()
    
    db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
    db_session.add(WorkspaceMember(user_id=member_user.id, workspace_id=workspace.id, role="member"))
    db_session.commit()
    
    mock_user.id = member_user.id
    response = client.delete(f"/workspaces/{workspace.id}/leave")
    assert response.status_code == 200
    
    member_record = db_session.query(WorkspaceMember).filter(WorkspaceMember.user_id == member_user.id, WorkspaceMember.workspace_id == workspace.id).first()
    assert member_record is None
    
    workspace_record = db_session.query(Workspace).filter(Workspace.id == workspace.id).first()
    assert workspace_record is not None


def test_leave_workspace_as_owner_transfers_successfully(db_session, mock_user):
    owner = User(username="ws_owner2", email="owner2@example.com", is_verified=True)
    admin_user = User(username="ws_admin", email="admin@example.com", is_verified=True)
    db_session.add(owner)
    db_session.add(admin_user)
    db_session.flush()
    
    workspace = Workspace(name="Transfer Workspace", created_by=owner.id, invite_code="leave2", invite_link="link2")
    db_session.add(workspace)
    db_session.flush()
    
    db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
    db_session.add(WorkspaceMember(user_id=admin_user.id, workspace_id=workspace.id, role="admin"))
    db_session.commit()
    
    mock_user.id = owner.id
    response = client.delete(f"/workspaces/{workspace.id}/leave")
    assert response.status_code == 200
    
    db_session.refresh(workspace)
    assert workspace.created_by == admin_user.id
    
    admin_membership = db_session.query(WorkspaceMember).filter(WorkspaceMember.user_id == admin_user.id, WorkspaceMember.workspace_id == workspace.id).first()
    assert admin_membership.role == "owner"
    
    owner_membership = db_session.query(WorkspaceMember).filter(WorkspaceMember.user_id == owner.id, WorkspaceMember.workspace_id == workspace.id).first()
    assert owner_membership is None


def test_leave_workspace_as_owner_fails_without_admin(db_session, mock_user):
    owner = User(username="ws_owner3", email="owner3@example.com", is_verified=True)
    regular_member = User(username="stranded_member", email="stranded@example.com", is_verified=True)
    db_session.add_all([owner, regular_member])
    db_session.flush()
    
    workspace = Workspace(name="No Admin Workspace", created_by=owner.id, invite_code="leave3", invite_link="link3")
    db_session.add(workspace)
    db_session.flush()
    
    db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
    db_session.add(WorkspaceMember(user_id=regular_member.id, workspace_id=workspace.id, role="member"))
    db_session.commit()
    
    mock_user.id = owner.id
    response = client.delete(f"/workspaces/{workspace.id}/leave")
    
    assert response.status_code == 400
    assert "Please promote a member to admin" in response.json()["detail"]

def test_leave_workspace_not_found(db_session, mock_user):
    mock_user.id = 1
    response = client.delete("/workspaces/9999/leave")
    assert response.status_code == 404
    assert response.json()["detail"] == "Workspace not found"


def test_leave_workspace_not_a_member(db_session, mock_user):
    owner = User(username="ws_owner", email="owner@example.com", is_verified=True)
    non_member = User(username="non_member", email="nonmember@example.com", is_verified=True)
    db_session.add(owner)
    db_session.add(non_member)
    db_session.flush()

    workspace = Workspace(name="Test Workspace", created_by=owner.id, invite_code="leave_code_1", invite_link="link_1")
    db_session.add(workspace)
    db_session.flush()

    db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
    db_session.commit()

    mock_user.id = non_member.id
    response = client.delete(f"/workspaces/{workspace.id}/leave")
    assert response.status_code == 404
    assert response.json()["detail"] == "You are not a member of this workspace"
    


# Update Workspace Name tests

def test_update_workspace_name_success_as_owner(db_session, mock_user):
	owner = User(username="rename_owner", email="rename_owner@example.com", is_verified=True)
	db_session.add(owner)
	db_session.flush()

	workspace = Workspace(name="Old Name", created_by=owner.id, invite_code="rename1", invite_link="link_rename1")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.commit()

	mock_user.id = owner.id
	response = client.patch(f"/workspaces/{workspace.id}", json={"name": "New Name"})

	assert response.status_code == 200
	assert response.json() == {"workspace_id": workspace.id, "name": "New Name"}

	db_session.refresh(workspace)
	assert workspace.name == "New Name"


def test_update_workspace_name_success_as_admin(db_session, mock_user):
	owner = User(username="rename_owner2", email="rename_owner2@example.com", is_verified=True)
	admin_user = User(username="rename_admin", email="rename_admin@example.com", is_verified=True)
	db_session.add_all([owner, admin_user])
	db_session.flush()

	workspace = Workspace(name="Old Name", created_by=owner.id, invite_code="rename2", invite_link="link_rename2")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.add(WorkspaceMember(user_id=admin_user.id, workspace_id=workspace.id, role="admin"))
	db_session.commit()

	mock_user.id = admin_user.id
	response = client.patch(f"/workspaces/{workspace.id}", json={"name": "Admin Renamed"})

	assert response.status_code == 200
	assert response.json() == {"workspace_id": workspace.id, "name": "Admin Renamed"}


def test_update_workspace_name_forbidden_for_regular_member(db_session, mock_user):
	owner = User(username="rename_owner3", email="rename_owner3@example.com", is_verified=True)
	member_user = User(username="rename_member", email="rename_member@example.com", is_verified=True)
	db_session.add_all([owner, member_user])
	db_session.flush()

	workspace = Workspace(name="Old Name", created_by=owner.id, invite_code="rename3", invite_link="link_rename3")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.add(WorkspaceMember(user_id=member_user.id, workspace_id=workspace.id, role="member"))
	db_session.commit()

	mock_user.id = member_user.id
	response = client.patch(f"/workspaces/{workspace.id}", json={"name": "Hacked Name"})

	assert response.status_code == 403
	assert response.json()["detail"] == "Only the workspace owner or an admin can configure workspace settings"

	db_session.refresh(workspace)
	assert workspace.name == "Old Name"


def test_update_workspace_name_not_found(db_session, mock_user):
	mock_user.id = 1
	response = client.patch("/workspaces/9999", json={"name": "Doesn't Matter"})

	assert response.status_code == 404
	assert response.json()["detail"] == "Workspace not found"


def test_update_workspace_name_not_a_member(db_session, mock_user):
	owner = User(username="rename_owner4", email="rename_owner4@example.com", is_verified=True)
	non_member = User(username="rename_stranger", email="rename_stranger@example.com", is_verified=True)
	db_session.add_all([owner, non_member])
	db_session.flush()

	workspace = Workspace(name="Old Name", created_by=owner.id, invite_code="rename4", invite_link="link_rename4")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.commit()

	mock_user.id = non_member.id
	response = client.patch(f"/workspaces/{workspace.id}", json={"name": "Sneaky Rename"})

	assert response.status_code == 404
	assert response.json()["detail"] == "You are not a member of this workspace"


def test_update_workspace_name_dangerous_input(db_session, mock_user):
	owner = User(username="rename_owner5", email="rename_owner5@example.com", is_verified=True)
	db_session.add(owner)
	db_session.flush()

	workspace = Workspace(name="Old Name", created_by=owner.id, invite_code="rename5", invite_link="link_rename5")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.commit()

	mock_user.id = owner.id
	response = client.patch(f"/workspaces/{workspace.id}", json={"name": "<script>alert(1)</script>"})

	assert response.status_code == 400
	assert response.json()["detail"] == "Invalid name, contains dangerous characters"

	db_session.refresh(workspace)
	assert workspace.name == "Old Name"


def test_update_workspace_name_strips_whitespace(db_session, mock_user):
	owner = User(username="rename_owner6", email="rename_owner6@example.com", is_verified=True)
	db_session.add(owner)
	db_session.flush()

	workspace = Workspace(name="Old Name", created_by=owner.id, invite_code="rename6", invite_link="link_rename6")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.commit()

	mock_user.id = owner.id
	response = client.patch(f"/workspaces/{workspace.id}", json={"name": "  Padded Name  "})

	assert response.status_code == 200
	assert response.json()["name"] == "Padded Name"

	db_session.refresh(workspace)
	assert workspace.name == "Padded Name"


def test_leave_workspace_owner_sole_member_deletes_workspace(db_session, mock_user):
    from models.workspace_integration import WorkspaceIntegrations

    owner = User(username="solo_owner", email="solo@example.com", is_verified=True)
    db_session.add(owner)
    db_session.flush()

    workspace = Workspace(name="Solo Workspace", created_by=owner.id, invite_code="solo1", invite_link="linksolo1")
    db_session.add(workspace)
    db_session.flush()

    db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
    db_session.add(WorkspaceIntegrations(workspace_id=workspace.id))
    db_session.commit()

    db_session.add(WorkspaceData(integration_id=workspace.id, type="task", source="jira", title="Cascade Task"))
    db_session.commit()
	
    mock_user.id = owner.id
    response = client.delete(f"/workspaces/{workspace.id}/leave")
    
    assert response.status_code == 200
    assert "Workspace deleted successfully as you were the only member" in response.json()["message"]
    assert db_session.query(WorkspaceData).filter(WorkspaceData.integration_id == workspace.id).first() is None
    assert db_session.query(Workspace).filter(Workspace.id == workspace.id).first() is None
    assert db_session.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id).first() is None
    assert db_session.query(WorkspaceIntegrations).filter(WorkspaceIntegrations.workspace_id == workspace.id).first() is None

#Delete workspace tests

def test_delete_workspace_success(db_session, mock_user):
    

    owner = User(username="del_owner", email="del_owner@example.com", is_verified=True)
    db_session.add(owner)
    db_session.flush()

    workspace = Workspace(name="To Delete", created_by=owner.id, invite_code="del1", invite_link="linkdel1")
    db_session.add(workspace)
    db_session.flush()

    member = WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner")
    integration = WorkspaceIntegrations(workspace_id=workspace.id)
    db_session.add_all([member, integration])
    db_session.flush()

    data_row = WorkspaceData(integration_id=workspace.id, type="task", source="jira", title="Cascade Task")
    db_session.add(data_row)
    db_session.commit()

    mock_user.id = owner.id
    response = client.delete(f"/workspaces/{workspace.id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Workspace deleted successfully"

    assert db_session.query(Workspace).filter(Workspace.id == workspace.id).first() is None
    assert db_session.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id).first() is None
    assert db_session.query(WorkspaceIntegrations).filter(WorkspaceIntegrations.workspace_id == workspace.id).first() is None
    assert db_session.query(WorkspaceData).filter(WorkspaceData.integration_id == workspace.id).first() is None
    


def test_delete_workspace_forbidden_for_member(db_session, mock_user):
    owner = User(username="del_owner2", email="del_owner2@example.com", is_verified=True)
    member_user = User(username="del_member", email="del_member@example.com", is_verified=True)
    db_session.add_all([owner, member_user])
    db_session.flush()

    workspace = Workspace(name="Stay Alive", created_by=owner.id, invite_code="del2", invite_link="linkdel2")
    db_session.add(workspace)
    db_session.flush()

    db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
    db_session.add(WorkspaceMember(user_id=member_user.id, workspace_id=workspace.id, role="member"))
    db_session.commit()

    mock_user.id = member_user.id
    response = client.delete(f"/workspaces/{workspace.id}")
    assert response.status_code == 403
    assert "Only the workspace owner" in response.json()["detail"]

    assert db_session.query(Workspace).filter(Workspace.id == workspace.id).first() is not None


def test_delete_workspace_not_found(db_session, mock_user):
    mock_user.id = 1
    response = client.delete("/workspaces/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Workspace not found"


#Generate invite code tests

def test_rotate_invite_code_success_as_owner(db_session, mock_user):
    owner = User(username="rot_owner", email="rot_owner@example.com", is_verified=True)
    db_session.add(owner)
    db_session.flush()

    workspace = Workspace(name="Rotate WS", created_by=owner.id, invite_code="oldcode123", invite_link="linkold")
    db_session.add(workspace)
    db_session.flush()

    member = WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner")
    db_session.add(member)
    db_session.commit()

    mock_user.id = owner.id
    response = client.patch(f"/workspaces/{workspace.id}/invite-code")

    assert response.status_code == 200
    data = response.json()
    assert data["workspace_id"] == workspace.id
    assert data["invite_code"] != "oldcode123"
    assert data["invite_link"].endswith(data["invite_code"])

    db_session.refresh(workspace)
    assert workspace.invite_code == data["invite_code"]


def test_rotate_invite_code_success_as_admin(db_session, mock_user):
    owner = User(username="rot_owner2", email="rot_owner2@example.com", is_verified=True)
    admin_user = User(username="rot_admin", email="rot_admin@example.com", is_verified=True)
    db_session.add_all([owner, admin_user])
    db_session.flush()

    workspace = Workspace(name="Rotate WS Admin", created_by=owner.id, invite_code="oldcode456", invite_link="linkold2")
    db_session.add(workspace)
    db_session.flush()

    db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
    db_session.add(WorkspaceMember(user_id=admin_user.id, workspace_id=workspace.id, role="admin"))
    db_session.commit()

    mock_user.id = admin_user.id
    response = client.patch(f"/workspaces/{workspace.id}/invite-code")
    assert response.status_code == 200


def test_rotate_invite_code_forbidden_for_regular_member(db_session, mock_user):
    owner = User(username="rot_owner3", email="rot_owner3@example.com", is_verified=True)
    member_user = User(username="rot_member", email="rot_member@example.com", is_verified=True)
    db_session.add_all([owner, member_user])
    db_session.flush()

    workspace = Workspace(name="Secure WS", created_by=owner.id, invite_code="secure123", invite_link="linksecure")
    db_session.add(workspace)
    db_session.flush()

    db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
    db_session.add(WorkspaceMember(user_id=member_user.id, workspace_id=workspace.id, role="member"))
    db_session.commit()

    mock_user.id = member_user.id
    response = client.patch(f"/workspaces/{workspace.id}/invite-code")

    assert response.status_code == 403
    assert "Only workspace owners or admins" in response.json()["detail"]


def test_rotate_invite_code_not_found(db_session, mock_user):
    mock_user.id = 1
    response = client.patch("/workspaces/9999/invite-code")
    assert response.status_code == 404
    assert response.json()["detail"] == "Workspace not found"


def test_rotate_invite_code_collision_handling():
    mock_user = make_mock_user(user_id=1)
    mock_workspace = make_mock_workspace(workspace_id=10)
    mock_member = MagicMock()
    mock_member.role = "owner"

    mock_db = MagicMock()

    def query_side_effect(model):
        mock_query = MagicMock()
        if model == WorkspaceMember:
            mock_query.filter.return_value.first.return_value = mock_member
        elif model == Workspace:
            mock_query.filter.return_value.first.return_value = mock_workspace
            mock_query.count.return_value = 3  # any real int works
        return mock_query

    mock_db.query.side_effect = query_side_effect
    
    mock_db.commit.side_effect = [IntegrityError(None, None, None), None]

    override_dependencies(mock_user, mock_db)

    with patch("secrets.token_urlsafe") as mock_token:
        mock_token.side_effect = ["colliding_code", "clean_code"]

        response = client.patch("/workspaces/10/invite-code")

    assert response.status_code == 200
    assert response.json()["invite_code"] == "clean_code"
    assert mock_db.commit.call_count == 2
    assert mock_db.rollback.call_count == 1

    clear_dependencies()
