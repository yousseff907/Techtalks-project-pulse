import pytest

from datetime import datetime, timedelta, timezone
import itertools
from unittest.mock import MagicMock, Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import app

from models.user import User
from models.workspace import Workspace
from models.workspace_data import WorkspaceData
from models.workspace_integration import WorkspaceIntegrations
from models.workspace_member import WorkspaceMember

from utils.database import get_db
from utils.dependencies import get_current_user

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


_test_user_counter = itertools.count(1)


def create_test_user(db_session, username=None, email=None):
    n = next(_test_user_counter)
    user = User(
        username=username or f"testuser{n}",
        email=email or f"test{n}@example.com",
        is_verified=True,
    )

    db_session.add(user)
    db_session.flush()

    return user


def create_workspace(db_session, user):
    workspace = Workspace(
        name="Workspace",
        created_by=user.id,
        invite_code="abc",
        invite_link="abc",
    )

    db_session.add(workspace)
    db_session.flush()

    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user.id,
        role="owner",
    )

    integration = WorkspaceIntegrations(
        workspace_id=workspace.id,
    )

    db_session.add(member)
    db_session.add(integration)
    db_session.flush()

    return workspace

def test_workspace_creation(db_session: Session, mock_user: Mock):
     
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
     
    response = client.post("/workspaces", json={"name": "   "})
    assert response.status_code == 400
    assert response.json()["detail"] == "Name cannot be blank"



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

def test_leave_workspace_as_member_success(db_session: Session, mock_user: Mock):
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


def test_leave_workspace_as_owner_transfers_successfully(db_session: Session, mock_user: Mock):
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


def test_leave_workspace_as_owner_fails_without_admin(db_session: Session, mock_user: Mock):
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

def test_leave_workspace_not_found(db_session: Session, mock_user: Mock):
    mock_user.id = 1
    response = client.delete("/workspaces/9999/leave")
    assert response.status_code == 404
    assert response.json()["detail"] == "Workspace not found"


def test_leave_workspace_not_a_member(db_session: Session, mock_user: Mock):
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

def test_update_workspace_name_success_as_owner(db_session: Session, mock_user: Mock):
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


def test_update_workspace_name_success_as_admin(db_session: Session, mock_user: Mock):
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


def test_update_workspace_name_forbidden_for_regular_member(db_session: Session, mock_user: Mock):
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


def test_update_workspace_name_not_found(db_session: Session, mock_user: Mock):
    mock_user.id = 1
    response = client.patch("/workspaces/9999", json={"name": "Doesn't Matter"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Workspace not found"


def test_update_workspace_name_not_a_member(db_session: Session, mock_user: Mock):
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


def test_update_workspace_name_dangerous_input(db_session: Session, mock_user: Mock):
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

    response = client.patch(f"/workspaces/{workspace.id}", json={"name": "   "})
    assert response.status_code == 400
    assert response.json()["detail"] == "Name cannot be blank"


def test_update_workspace_name_strips_whitespace(db_session: Session, mock_user: Mock):
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


def test_leave_workspace_owner_sole_member_deletes_workspace(db_session: Session, mock_user: Mock):
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

def test_delete_workspace_success(db_session: Session, mock_user: Mock):
    

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
    


def test_delete_workspace_forbidden_for_member(db_session: Session, mock_user: Mock):
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


def test_delete_workspace_not_found(db_session: Session, mock_user: Mock):
    mock_user.id = 1
    response = client.delete("/workspaces/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Workspace not found"


#Generate invite code tests

def test_rotate_invite_code_success_as_owner(db_session: Session, mock_user: Mock):
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


def test_rotate_invite_code_success_as_admin(db_session: Session, mock_user: Mock):
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


def test_rotate_invite_code_forbidden_for_regular_member(db_session: Session, mock_user: Mock):
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


def test_rotate_invite_code_not_found(db_session: Session, mock_user: Mock):
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

# Get Workspace Details tests

def test_get_workspace_details_success_as_owner(db_session: Session, mock_user: Mock):
	owner = User(username="details_owner", email="details_owner@example.com", is_verified=True)
	db_session.add(owner)
	db_session.flush()

	workspace = Workspace(name="Details Workspace", created_by=owner.id, invite_code="details1", invite_link="link_details1")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.commit()

	mock_user.id = owner.id
	response = client.get(f"/workspaces/{workspace.id}")

	assert response.status_code == 200
	body = response.json()
	assert body["id"] == workspace.id
	assert body["name"] == "Details Workspace"
	assert body["invite_code"] == "details1"
	assert body["invite_link"] == "link_details1"
	assert body["created_by"] == "details_owner"
	assert body["member_count"] == 1
	assert body["created_at"] is not None


def test_get_workspace_details_success_as_regular_member(db_session: Session, mock_user: Mock):
	owner = User(username="details_owner2", email="details_owner2@example.com", is_verified=True)
	member_user = User(username="details_member", email="details_member@example.com", is_verified=True)
	db_session.add_all([owner, member_user])
	db_session.flush()

	workspace = Workspace(name="Shared Details WS", created_by=owner.id, invite_code="details2", invite_link="link_details2")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.add(WorkspaceMember(user_id=member_user.id, workspace_id=workspace.id, role="member"))
	db_session.commit()

	mock_user.id = member_user.id
	response = client.get(f"/workspaces/{workspace.id}")

	assert response.status_code == 200
	body = response.json()
	assert body["created_by"] == "details_owner2"
	assert body["member_count"] == 2


def test_get_workspace_details_not_found(db_session: Session, mock_user: Mock):
	mock_user.id = 1
	response = client.get("/workspaces/9999")

	assert response.status_code == 404
	assert response.json()["detail"] == "Workspace not found"


def test_get_workspace_details_not_found_before_membership_check(db_session: Session, mock_user: Mock):
	# Confirms a non-existent workspace returns 404, not 403, even though
	# no membership row could possibly exist for it either.
	mock_user.id = 1
	response = client.get("/workspaces/123456")

	assert response.status_code == 404
	assert response.json()["detail"] == "Workspace not found"


def test_get_workspace_details_forbidden_for_non_member(db_session: Session, mock_user: Mock):
	owner = User(username="details_owner3", email="details_owner3@example.com", is_verified=True)
	non_member = User(username="details_stranger", email="details_stranger@example.com", is_verified=True)
	db_session.add_all([owner, non_member])
	db_session.flush()

	workspace = Workspace(name="Private WS", created_by=owner.id, invite_code="details3", invite_link="link_details3")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.commit()

	mock_user.id = non_member.id
	response = client.get(f"/workspaces/{workspace.id}")

	assert response.status_code == 403
	assert response.json()["detail"] == "You are not a member of this workspace"


def test_get_workspace_details_member_count_accurate(db_session: Session, mock_user: Mock):
	owner = User(username="details_owner4", email="details_owner4@example.com", is_verified=True)
	member_a = User(username="details_member_a", email="details_member_a@example.com", is_verified=True)
	member_b = User(username="details_member_b", email="details_member_b@example.com", is_verified=True)
	db_session.add_all([owner, member_a, member_b])
	db_session.flush()

	workspace = Workspace(name="Count WS", created_by=owner.id, invite_code="details4", invite_link="link_details4")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.add(WorkspaceMember(user_id=member_a.id, workspace_id=workspace.id, role="member"))
	db_session.add(WorkspaceMember(user_id=member_b.id, workspace_id=workspace.id, role="admin"))
	db_session.commit()

	mock_user.id = owner.id
	response = client.get(f"/workspaces/{workspace.id}")

	assert response.status_code == 200
	assert response.json()["member_count"] == 3


def test_get_workspace_details_created_by_deleted_user(db_session: Session, mock_user: Mock):
	owner = User(username="details_owner5", email="details_owner5@example.com", is_verified=True)
	member_user = User(username="details_member5", email="details_member5@example.com", is_verified=True)
	db_session.add_all([owner, member_user])
	db_session.flush()

	workspace = Workspace(name="Orphaned WS", created_by=owner.id, invite_code="details5", invite_link="link_details5")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=member_user.id, workspace_id=workspace.id, role="owner"))
	db_session.commit()

	# Simulate created_by referencing a user that no longer exists,
	# e.g. via ON DELETE SET NULL from a path outside normal account deletion.
	workspace.created_by = None
	db_session.commit()

	mock_user.id = member_user.id
	response = client.get(f"/workspaces/{workspace.id}")

	assert response.status_code == 200
	assert response.json()["created_by"] == "Deleted User"

# Get Sync Status tests

def test_get_sync_status_success(db_session: Session, mock_user: Mock):
	owner = User(username="sync_status_owner", email="sync_status_owner@example.com", is_verified=True)
	db_session.add(owner)
	db_session.flush()

	workspace = Workspace(name="Sync Status WS", created_by=owner.id, invite_code="syncstatus1", invite_link="link_syncstatus1")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.add(WorkspaceIntegrations(workspace_id=workspace.id))
	db_session.commit()

	mock_user.id = owner.id
	response = client.get(f"/workspaces/{workspace.id}/sync/status")

	assert response.status_code == 200
	assert "last_synced_at" in response.json()
	assert response.json()["last_synced_at"] is None


def test_get_sync_status_reflects_updated_timestamp(db_session: Session, mock_user: Mock):
	owner = User(username="sync_status_owner2", email="sync_status_owner2@example.com", is_verified=True)
	db_session.add(owner)
	db_session.flush()

	workspace = Workspace(name="Sync Status WS 2", created_by=owner.id, invite_code="syncstatus2", invite_link="link_syncstatus2")
	db_session.add(workspace)
	db_session.flush()

	integration = WorkspaceIntegrations(workspace_id=workspace.id)
	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.add(integration)
	db_session.commit()

	from datetime import datetime, timezone
	integration.last_synced_at = datetime.now(timezone.utc)
	db_session.commit()

	mock_user.id = owner.id
	response = client.get(f"/workspaces/{workspace.id}/sync/status")

	assert response.status_code == 200
	assert response.json()["last_synced_at"] is not None


def test_get_sync_status_workspace_not_found(db_session: Session, mock_user: Mock):
	mock_user.id = 1
	response = client.get("/workspaces/9999/sync/status")

	assert response.status_code == 404
	assert response.json()["detail"] == "Workspace not found"


def test_get_sync_status_forbidden_for_non_member(db_session: Session, mock_user: Mock):
	owner = User(username="sync_status_owner3", email="sync_status_owner3@example.com", is_verified=True)
	non_member = User(username="sync_status_stranger", email="sync_status_stranger@example.com", is_verified=True)
	db_session.add_all([owner, non_member])
	db_session.flush()

	workspace = Workspace(name="Private Sync WS", created_by=owner.id, invite_code="syncstatus3", invite_link="link_syncstatus3")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.add(WorkspaceIntegrations(workspace_id=workspace.id))
	db_session.commit()

	mock_user.id = non_member.id
	response = client.get(f"/workspaces/{workspace.id}/sync/status")

	assert response.status_code == 403
	assert response.json()["detail"] == "You are not a member of this workspace"


def test_get_sync_status_no_integration(db_session: Session, mock_user: Mock):
	owner = User(username="sync_status_owner4", email="sync_status_owner4@example.com", is_verified=True)
	db_session.add(owner)
	db_session.flush()

	workspace = Workspace(name="No Integration WS", created_by=owner.id, invite_code="syncstatus4", invite_link="link_syncstatus4")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.commit()

	mock_user.id = owner.id
	response = client.get(f"/workspaces/{workspace.id}/sync/status")

	assert response.status_code == 404


# Manual Sync tests

def test_manual_sync_success_as_owner(db_session: Session, mock_user: Mock, mock_redis_client: MagicMock):
	owner = User(username="manual_sync_owner", email="manual_sync_owner@example.com", is_verified=True)
	db_session.add(owner)
	db_session.flush()

	workspace = Workspace(name="Manual Sync WS", created_by=owner.id, invite_code="manualsync1", invite_link="link_manualsync1")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.add(WorkspaceIntegrations(workspace_id=workspace.id))
	db_session.commit()

	mock_redis_client.exists.return_value = False

	mock_task = MagicMock()
	mock_task.id = "fake-task-id-123"

	mock_user.id = owner.id
	with patch("routes.workspaces.sync_workspace_data") as mock_sync_task:
		mock_sync_task.delay.return_value = mock_task
		response = client.post(f"/workspaces/{workspace.id}/sync")

	assert response.status_code == 202
	assert response.json() == {"task_id": "fake-task-id-123", "status": "queued"}

	mock_sync_task.delay.assert_called_once_with(workspace.id)
	mock_redis_client.setex.assert_called_once_with(f"sync_cooldown:{workspace.id}", 300, "1")


def test_manual_sync_success_as_admin(db_session: Session, mock_user: Mock, mock_redis_client: MagicMock):
	owner = User(username="manual_sync_owner2", email="manual_sync_owner2@example.com", is_verified=True)
	admin_user = User(username="manual_sync_admin", email="manual_sync_admin@example.com", is_verified=True)
	db_session.add_all([owner, admin_user])
	db_session.flush()

	workspace = Workspace(name="Manual Sync WS Admin", created_by=owner.id, invite_code="manualsync2", invite_link="link_manualsync2")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.add(WorkspaceMember(user_id=admin_user.id, workspace_id=workspace.id, role="admin"))
	db_session.add(WorkspaceIntegrations(workspace_id=workspace.id))
	db_session.commit()

	mock_redis_client.exists.return_value = False

	mock_task = MagicMock()
	mock_task.id = "fake-task-id-456"

	mock_user.id = admin_user.id
	with patch("routes.workspaces.sync_workspace_data") as mock_sync_task:
		mock_sync_task.delay.return_value = mock_task
		response = client.post(f"/workspaces/{workspace.id}/sync")

	assert response.status_code == 202


def test_manual_sync_forbidden_for_regular_member(db_session: Session, mock_user: Mock, mock_redis_client: MagicMock):
	owner = User(username="manual_sync_owner3", email="manual_sync_owner3@example.com", is_verified=True)
	member_user = User(username="manual_sync_member", email="manual_sync_member@example.com", is_verified=True)
	db_session.add_all([owner, member_user])
	db_session.flush()

	workspace = Workspace(name="Manual Sync WS Member", created_by=owner.id, invite_code="manualsync3", invite_link="link_manualsync3")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.add(WorkspaceMember(user_id=member_user.id, workspace_id=workspace.id, role="member"))
	db_session.add(WorkspaceIntegrations(workspace_id=workspace.id))
	db_session.commit()

	mock_user.id = member_user.id
	with patch("routes.workspaces.sync_workspace_data") as mock_sync_task:
		response = client.post(f"/workspaces/{workspace.id}/sync")

	assert response.status_code == 403
	assert response.json()["detail"] == "Only workspace owners or admins can trigger a manual sync"
	mock_sync_task.delay.assert_not_called()


def test_manual_sync_workspace_not_found(db_session: Session, mock_user: Mock):
	mock_user.id = 1
	response = client.post("/workspaces/9999/sync")

	assert response.status_code == 404
	assert response.json()["detail"] == "Workspace not found"


def test_manual_sync_not_a_member(db_session: Session, mock_user: Mock):
	owner = User(username="manual_sync_owner4", email="manual_sync_owner4@example.com", is_verified=True)
	non_member = User(username="manual_sync_stranger", email="manual_sync_stranger@example.com", is_verified=True)
	db_session.add_all([owner, non_member])
	db_session.flush()

	workspace = Workspace(name="Manual Sync WS Stranger", created_by=owner.id, invite_code="manualsync4", invite_link="link_manualsync4")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.add(WorkspaceIntegrations(workspace_id=workspace.id))
	db_session.commit()

	mock_user.id = non_member.id
	response = client.post(f"/workspaces/{workspace.id}/sync")

	assert response.status_code == 403
	assert response.json()["detail"] == "You are not a member of this workspace"


def test_manual_sync_no_integration(db_session: Session, mock_user: Mock):
	owner = User(username="manual_sync_owner5", email="manual_sync_owner5@example.com", is_verified=True)
	db_session.add(owner)
	db_session.flush()

	workspace = Workspace(name="Manual Sync No Integration", created_by=owner.id, invite_code="manualsync5", invite_link="link_manualsync5")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.commit()

	mock_user.id = owner.id
	response = client.post(f"/workspaces/{workspace.id}/sync")

	assert response.status_code == 404


def test_manual_sync_cooldown_active_returns_429(db_session: Session, mock_user: Mock, mock_redis_client: MagicMock):
	owner = User(username="manual_sync_owner6", email="manual_sync_owner6@example.com", is_verified=True)
	db_session.add(owner)
	db_session.flush()

	workspace = Workspace(name="Manual Sync Cooldown WS", created_by=owner.id, invite_code="manualsync6", invite_link="link_manualsync6")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.add(WorkspaceIntegrations(workspace_id=workspace.id))
	db_session.commit()

	mock_redis_client.exists.return_value = True

	mock_user.id = owner.id
	with patch("routes.workspaces.sync_workspace_data") as mock_sync_task:
		response = client.post(f"/workspaces/{workspace.id}/sync")

	assert response.status_code == 429
	assert response.json()["detail"] == "A sync was recently triggered, please wait before trying again"
	mock_sync_task.delay.assert_not_called()
	mock_redis_client.setex.assert_not_called()


def test_manual_sync_checks_correct_cooldown_key(db_session: Session, mock_user: Mock, mock_redis_client: MagicMock):
	owner = User(username="manual_sync_owner7", email="manual_sync_owner7@example.com", is_verified=True)
	db_session.add(owner)
	db_session.flush()

	workspace = Workspace(name="Manual Sync Key Check WS", created_by=owner.id, invite_code="manualsync7", invite_link="link_manualsync7")
	db_session.add(workspace)
	db_session.flush()

	db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
	db_session.add(WorkspaceIntegrations(workspace_id=workspace.id))
	db_session.commit()

	mock_redis_client.exists.return_value = False
	mock_task = MagicMock()
	mock_task.id = "fake-task-id-789"

	mock_user.id = owner.id
	with patch("routes.workspaces.sync_workspace_data") as mock_sync_task:
		mock_sync_task.delay.return_value = mock_task
		client.post(f"/workspaces/{workspace.id}/sync")

	mock_redis_client.exists.assert_called_once_with(f"sync_cooldown:{workspace.id}")
     
# ---- List workspaces tests ----

def test_list_workspaces_returns_user_workspaces(db_session: Session, mock_user: Mock):
    user = User(username="list_user", email="list_user@example.com", is_verified=True)
    other_owner = User(username="other_owner", email="other@example.com", is_verified=True)
    db_session.add_all([user, other_owner])
    db_session.flush()

    ws1 = Workspace(name="First WS", created_by=user.id, invite_code="listcode1", invite_link="listlink1")
    ws2 = Workspace(name="Second WS", created_by=other_owner.id, invite_code="listcode2", invite_link="listlink2")
    ws3 = Workspace(name="Not Mine WS", created_by=other_owner.id, invite_code="listcode3", invite_link="listlink3")
    db_session.add_all([ws1, ws2, ws3])
    db_session.flush()

    db_session.add(WorkspaceMember(user_id=user.id, workspace_id=ws1.id, role="owner"))
    db_session.add(WorkspaceMember(user_id=user.id, workspace_id=ws2.id, role="admin"))
    db_session.add(WorkspaceMember(user_id=other_owner.id, workspace_id=ws3.id, role="owner"))
    db_session.commit()

    mock_user.id = user.id
    response = client.get("/workspaces")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2

    workspaces_by_id = {ws["id"]: ws for ws in body}
    assert workspaces_by_id[ws1.id]["id"] == ws1.id
    assert workspaces_by_id[ws1.id]["name"] == "First WS"
    assert workspaces_by_id[ws1.id]["role"] == "owner"
    assert workspaces_by_id[ws1.id]["member_count"] == 1
    assert "created_at" in workspaces_by_id[ws1.id]
    assert workspaces_by_id[ws2.id]["id"] == ws2.id
    assert workspaces_by_id[ws2.id]["name"] == "Second WS"
    assert workspaces_by_id[ws2.id]["role"] == "admin"
    assert workspaces_by_id[ws2.id]["member_count"] == 1
    assert "created_at" in workspaces_by_id[ws2.id]
   



def test_list_workspaces_returns_empty_list_when_no_memberships(db_session: Session, mock_user: Mock):
    user = User(username="loner_user", email="loner@example.com", is_verified=True)
    db_session.add(user)
    db_session.commit()

    mock_user.id = user.id
    response = client.get("/workspaces")
    
    assert response.status_code == 200
    assert response.json() == []


def test_list_workspaces_excludes_other_users_workspaces(db_session: Session, mock_user: Mock):
    user = User(username="me_user", email="me@example.com", is_verified=True)
    stranger = User(username="stranger", email="stranger@example.com", is_verified=True)
    db_session.add_all([user, stranger])
    db_session.flush()

    ws = Workspace(name="Stranger WS", created_by=stranger.id, invite_code="listcode4", invite_link="listlink4")
    db_session.add(ws)
    db_session.flush()

    db_session.add(WorkspaceMember(user_id=stranger.id, workspace_id=ws.id, role="owner"))
    db_session.commit()

    mock_user.id = user.id
    response = client.get("/workspaces")

    assert response.status_code == 200
    assert response.json() == []


def test_list_workspaces_includes_correct_role_per_workspace(db_session: Session, mock_user: Mock):
    user = User(username="multi_role_user", email="multi@example.com", is_verified=True)
    other = User(username="other_multi", email="other_multi@example.com", is_verified=True)
    db_session.add_all([user, other])
    db_session.flush()

    ws_owner = Workspace(name="Owned", created_by=user.id, invite_code="mrole1", invite_link="mlink1")
    ws_admin = Workspace(name="Admin Of", created_by=other.id, invite_code="mrole2", invite_link="mlink2")
    ws_member = Workspace(name="Member Of", created_by=other.id, invite_code="mrole3", invite_link="mlink3")
    db_session.add_all([ws_owner, ws_admin, ws_member])
    db_session.flush()

    db_session.add(WorkspaceMember(user_id=user.id, workspace_id=ws_owner.id, role="owner"))
    db_session.add(WorkspaceMember(user_id=user.id, workspace_id=ws_admin.id, role="admin"))
    db_session.add(WorkspaceMember(user_id=user.id, workspace_id=ws_member.id, role="member"))
    db_session.commit()

    mock_user.id = user.id
    response = client.get("/workspaces")

    assert response.status_code == 200
    body = response.json()

    roles_by_name = {ws["name"]: ws["role"] for ws in body}
    assert roles_by_name["Owned"] == "owner"
    assert roles_by_name["Admin Of"] == "admin"
    assert roles_by_name["Member Of"] == "member"

#List workspace members

def test_list_workspace_members_success(db_session: Session, mock_user: Mock):
    owner = User(username="owner", email="owner@example.com", is_verified=True)
    member = User(username="member", email="member@example.com", is_verified=True)
    db_session.add_all([owner, member])
    db_session.flush()

    workspace = Workspace(
        name="Members WS",
        created_by=owner.id,
        invite_code="members1",
        invite_link="link1",
    )
    db_session.add(workspace)
    db_session.flush()

    db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
    db_session.add(WorkspaceMember(user_id=member.id, workspace_id=workspace.id, role="member"))
    integration = WorkspaceIntegrations(workspace_id=workspace.id)

    db_session.add(integration)
    db_session.flush()

    db_session.add(
        WorkspaceData(
            integration_id=workspace.id,
            type="user",
            source="jira",
            payload={
                "id": "jira-owner",
                "name": "owner",
                "email": "owner@example.com",
            },
        )
    )

    db_session.add(
        WorkspaceData(
            integration_id=workspace.id,
            type="user",
            source="notion",
            payload={
                "id": "notion-member",
                "name": "member",
                "email": "member@example.com",
            },
        )
    )

    db_session.commit()

    mock_user.id = owner.id

    response = client.get(f"/workspaces/{workspace.id}/members")

    assert response.status_code == 200

    body = response.json()
    assert len(body) == 2

    owner_entry = next(x for x in body if x["username"] == "owner")
    member_entry = next(x for x in body if x["username"] == "member")

    assert owner_entry["jira"]["id"] == "jira-owner"
    assert owner_entry["notion"] is None

    assert member_entry["jira"] is None
    assert member_entry["notion"]["id"] == "notion-member"


def test_list_workspace_members_username_fallback(db_session: Session, mock_user: Mock):
    user = User(
        username="fallbackuser",
        email="platform@example.com",
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    workspace = Workspace(
        name="Fallback WS",
        created_by=user.id,
        invite_code="fallback",
        invite_link="link",
    )
    db_session.add(workspace)
    db_session.flush()

    db_session.add(
        WorkspaceMember(
            user_id=user.id,
            workspace_id=workspace.id,
            role="owner",
        )
    )

    integration = WorkspaceIntegrations(
        workspace_id=workspace.id
    )

    db_session.add(integration)
    db_session.flush()


    db_session.add(
        WorkspaceData(
            integration_id=workspace.id,
            type="user",
            source="jira",
            payload={
                "id": "jira1",
                "name": "fallbackuser",
                "email": "different@example.com",
            },
        )
    )

    db_session.commit()

    mock_user.id = user.id

    response = client.get(f"/workspaces/{workspace.id}/members")

    assert response.status_code == 200

    body = response.json()

    assert body[0]["jira"]["id"] == "jira1"


def test_list_workspace_members_email_precedence_over_username(db_session: Session, mock_user: Mock):
    user = User(
        username="john",
        email="john@example.com",
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    workspace = Workspace(
        name="Priority WS",
        created_by=user.id,
        invite_code="priority",
        invite_link="link",
    )
    db_session.add(workspace)
    db_session.flush()

    db_session.add(
        WorkspaceMember(
            user_id=user.id,
            workspace_id=workspace.id,
            role="owner",
        )
    )

    integration = WorkspaceIntegrations(
        workspace_id=workspace.id
    )

    db_session.add(integration)
    db_session.flush()

    db_session.add_all([
        WorkspaceData(
            integration_id=workspace.id,
            type="user",
            source="jira",
            payload={
                "id": "email-match",
                "name": "someoneelse",
                "email": "john@example.com",
            },
        ),
        WorkspaceData(
            integration_id=workspace.id,
            type="user",
            source="jira",
            payload={
                "id": "username-match",
                "name": "john",
                "email": "other@example.com",
            },
        ),
    ])

    db_session.commit()

    mock_user.id = user.id

    response = client.get(f"/workspaces/{workspace.id}/members")

    assert response.status_code == 200

    assert response.json()[0]["jira"]["id"] == "email-match"


def test_list_workspace_members_returns_null_when_no_synced_users(db_session: Session, mock_user: Mock):
    owner = User(
        username="owner",
        email="owner@example.com",
        is_verified=True,
    )
    db_session.add(owner)
    db_session.flush()

    workspace = Workspace(
        name="Empty Sync",
        created_by=owner.id,
        invite_code="empty",
        invite_link="link",
    )
    db_session.add(workspace)
    db_session.flush()

    db_session.add(
        WorkspaceMember(
            user_id=owner.id,
            workspace_id=workspace.id,
            role="owner",
        )
    )

    db_session.add(WorkspaceIntegrations(workspace_id=workspace.id))
    db_session.commit()

    mock_user.id = owner.id

    response = client.get(f"/workspaces/{workspace.id}/members")

    assert response.status_code == 200

    member = response.json()[0]

    assert member["jira"] is None
    assert member["notion"] is None

def test_list_workspace_members_workspace_not_found(db_session: Session, mock_user: Mock):
    mock_user.id = 1

    response = client.get("/workspaces/9999/members")

    assert response.status_code == 404
    assert response.json()["detail"] == "Workspace not found"

def test_list_workspace_members_forbidden_for_non_member(db_session: Session, mock_user: Mock):
    owner = User(
        username="owner",
        email="owner@example.com",
        is_verified=True,
    )
    stranger = User(
        username="stranger",
        email="stranger@example.com",
        is_verified=True,
    )

    db_session.add_all([owner, stranger])
    db_session.flush()

    workspace = Workspace(
        name="Private WS",
        created_by=owner.id,
        invite_code="private",
        invite_link="link",
    )

    db_session.add(workspace)
    db_session.flush()

    db_session.add(
        WorkspaceMember(
            user_id=owner.id,
            workspace_id=workspace.id,
            role="owner",
        )
    )

    db_session.commit()

    mock_user.id = stranger.id

    response = client.get(f"/workspaces/{workspace.id}/members")

    assert response.status_code == 403
    assert response.json()["detail"] == "You are not a member of this workspace"

def test_list_workspace_members_uses_latest_sync_batch(db_session: Session, mock_user: Mock):
    owner = User(
        username="owner",
        email="owner@example.com",
        is_verified=True,
    )
    db_session.add(owner)
    db_session.flush()

    workspace = Workspace(
        name="Latest Sync",
        created_by=owner.id,
        invite_code="latest",
        invite_link="link",
    )
    db_session.add(workspace)
    db_session.flush()

    db_session.add(
        WorkspaceMember(
            user_id=owner.id,
            workspace_id=workspace.id,
            role="owner",
        )
    )

    db_session.add(
        WorkspaceIntegrations(
            workspace_id=workspace.id,
        )
    )
    db_session.flush()

    old_time = datetime.now(timezone.utc) - timedelta(hours=1)
    new_time = datetime.now(timezone.utc)

    db_session.add(
        WorkspaceData(
            integration_id=workspace.id,
            type="user",
            source="jira",
            fetched_at=old_time,
            payload={
                "id": "jira-user-old",
                "name": "Old Name",
                "email": "owner@example.com",
            },
        )
    )

    db_session.add(
        WorkspaceData(
            integration_id=workspace.id,
            type="user",
            source="jira",
            fetched_at=new_time,
            payload={
                "id": "jira-user-new",
                "name": "New Name",
                "email": "owner@example.com",
            },
        )
    )

    db_session.commit()

    mock_user.id = owner.id

    response = client.get(f"/workspaces/{workspace.id}/members")

    assert response.status_code == 200

    member = response.json()[0]

    assert member["jira"]["id"] == "jira-user-new"
    assert member["jira"]["name"] == "New Name"
    assert member["jira"]["email"] == "owner@example.com"
    
def test_get_workspace_data_empty(db_session: Session):

    user = create_test_user(db_session)

    app.dependency_overrides[get_current_user] = lambda: user

    workspace = create_workspace(
        db_session,
        user,
    )

    response = client.get(
        f"/workspaces/{workspace.id}/data"
    )

    assert response.status_code == 200
    assert response.json() == []
    
def test_get_workspace_data_latest_batch(db_session: Session):

    user = create_test_user(db_session)

    app.dependency_overrides[get_current_user] = lambda: user

    workspace = create_workspace(
        db_session,
        user,
    )

    old_time = datetime.now(timezone.utc) - timedelta(days=1)
    new_time = datetime.now(timezone.utc)

    db_session.add(
        WorkspaceData(
            integration_id=workspace.id,
            type="task",
            source="jira",
            title="Old Task",
            status="DONE",
            fetched_at=old_time,
        )
    )

    db_session.add(
        WorkspaceData(
            integration_id=workspace.id,
            type="task",
            source="jira",
            title="New Task",
            status="TODO",
            fetched_at=new_time,
        )
    )

    db_session.commit()

    response = client.get(
        f"/workspaces/{workspace.id}/data"
    )

    
    assert response.status_code == 200
    data = response.json()
    titles = [item["title"] for item in data]

    assert len(data) == 1
    assert "New Task" in titles
    assert "Old Task" not in titles

def test_get_workspace_data_type_filter(db_session: Session):

    user = create_test_user(db_session)

    app.dependency_overrides[get_current_user] = lambda: user

    workspace = create_workspace(
        db_session,
        user,
    )

    now = datetime.now(timezone.utc)

    db_session.add_all([
        WorkspaceData(
            integration_id=workspace.id,
            type="task",
            source="jira",
            title="Task",
            fetched_at=now,
        ),
        WorkspaceData(
            integration_id=workspace.id,
            type="project",
            source="jira",
            title="Project",
            fetched_at=now,
        ),
    ])

    db_session.commit()

    response = client.get(
        f"/workspaces/{workspace.id}/data?type=task"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["type"] == "task"
    
def test_get_workspace_data_source_filter(db_session: Session):

    user = create_test_user(db_session)

    app.dependency_overrides[get_current_user] = lambda: user

    workspace = create_workspace(
        db_session,
        user,
    )

    now = datetime.now(timezone.utc)

    db_session.add_all([
        WorkspaceData(
            integration_id=workspace.id,
            type="task",
            source="jira",
            title="Jira Task",
            fetched_at=now,
        ),
        WorkspaceData(
            integration_id=workspace.id,
            type="task",
            source="notion",
            title="Notion Task",
            fetched_at=now,
        ),
    ])

    db_session.commit()

    response = client.get(
        f"/workspaces/{workspace.id}/data?source=jira"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["source"] == "jira"


def test_get_workspace_data_status_filter(db_session: Session):

    user = create_test_user(db_session)

    app.dependency_overrides[get_current_user] = lambda: user

    workspace = create_workspace(
        db_session,
        user,
    )

    now = datetime.now(timezone.utc)

    db_session.add_all([
        WorkspaceData(
            integration_id=workspace.id,
            type="task",
            source="jira",
            title="Done",
            status="DONE",
            fetched_at=now,
        ),
        WorkspaceData(
            integration_id=workspace.id,
            type="task",
            source="jira",
            title="Todo",
            status="TODO",
            fetched_at=now,
        ),
    ])

    db_session.commit()

    response = client.get(
        f"/workspaces/{workspace.id}/data?status=DONE"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "DONE"


def test_get_workspace_data_search(db_session: Session):

    user = create_test_user(db_session)

    app.dependency_overrides[get_current_user] = lambda: user

    workspace = create_workspace(
        db_session,
        user,
    )

    now = datetime.now(timezone.utc)

    db_session.add_all([
        WorkspaceData(
            integration_id=workspace.id,
            type="task",
            source="jira",
            title="Backend Login",
            fetched_at=now,
        ),
        WorkspaceData(
            integration_id=workspace.id,
            type="task",
            source="jira",
            title="Frontend",
            fetched_at=now,
        ),
    ])

    db_session.commit()

    response = client.get(
        f"/workspaces/{workspace.id}/data?search=backend"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Backend Login"

def test_get_workspace_data_combined_filters(db_session: Session):

    user = create_test_user(db_session)

    app.dependency_overrides[get_current_user] = lambda: user

    workspace = create_workspace(
        db_session,
        user,
    )

    now = datetime.now(timezone.utc)

    db_session.add_all([
        # Matches every filter: type, source, status, and search
        WorkspaceData(
            integration_id=workspace.id,
            type="task",
            source="jira",
            title="Backend Login",
            status="DONE",
            fetched_at=now,
        ),
        # Wrong status only
        WorkspaceData(
            integration_id=workspace.id,
            type="task",
            source="jira",
            title="Backend API",
            status="TODO",
            fetched_at=now,
        ),
        # Wrong type only
        WorkspaceData(
            integration_id=workspace.id,
            type="project",
            source="jira",
            title="Backend Design",
            status="DONE",
            fetched_at=now,
        ),
        # Wrong source only
        WorkspaceData(
            integration_id=workspace.id,
            type="task",
            source="notion",
            title="Backend Notion",
            status="DONE",
            fetched_at=now,
        ),
        # Wrong search term only
        WorkspaceData(
            integration_id=workspace.id,
            type="task",
            source="jira",
            title="Frontend Login",
            status="DONE",
            fetched_at=now,
        ),
    ])

    db_session.commit()

    response = client.get(
        f"/workspaces/{workspace.id}/data"
        "?type=task&source=jira&status=DONE&search=backend"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "Backend Login"
    assert data[0]["type"] == "task"
    assert data[0]["source"] == "jira"
    assert data[0]["status"] == "DONE"

def test_get_workspace_data_workspace_not_found(db_session: Session):

    user = create_test_user(db_session)

    app.dependency_overrides[get_current_user] = lambda: user

    response = client.get(
        "/workspaces/999999/data"
    )

    assert response.status_code == 404


def test_get_workspace_data_not_member(db_session: Session):

    user = create_test_user(db_session)

    app.dependency_overrides[get_current_user] = lambda: user

    other_user = create_test_user(db_session)

    workspace = Workspace(
        name="Private",
        created_by=other_user.id,
        invite_code="xyz",
        invite_link="xyz",
    )

    db_session.add(workspace)
    db_session.commit()

    response = client.get(
        f"/workspaces/{workspace.id}/data"
    )

    assert response.status_code == 403



#AI Summary Generation Tests


def test_generate_workspace_summary_success(db_session: Session, mock_user: Mock):
    owner = User(
        username="owner",
        email="owner@test.com",
        is_verified=True,
    )
    db_session.add(owner)
    db_session.flush()

    workspace = Workspace(
        name="Workspace",
        created_by=owner.id,
        invite_code="abc",
        invite_link="abc",
    )
    db_session.add(workspace)
    db_session.flush()

    db_session.add(
        WorkspaceMember(
            user_id=owner.id,
            workspace_id=workspace.id,
            role="owner",
        )
    )
    db_session.commit()

    mock_user.id = owner.id

    with patch(
        "routes.workspaces.generate_workspace_summary",
        return_value="Workspace summary",
    ):
        response = client.post(
            f"/workspaces/{workspace.id}/summary"
        )

    assert response.status_code == 200

    data = response.json()
    assert data == "Workspace summary"




def test_generate_workspace_summary_workspace_not_found(db_session: Session, mock_user: Mock):
    mock_user.id = 1

    user = create_test_user(db_session)

    app.dependency_overrides[get_current_user] = lambda: user

    workspace = create_workspace(
        db_session,
        user,
    )

    now = datetime.now(timezone.utc)

    db_session.add_all([
        WorkspaceData(
            integration_id=workspace.id,
            type="task",
            source="jira",
            title="Done",
            status="DONE",
            fetched_at=now,
        ),
        WorkspaceData(
            integration_id=workspace.id,
            type="task",
            source="jira",
            title="Todo",
            status="TODO",
            fetched_at=now,
        ),
    ])

    db_session.commit()

    response = client.get(
        f"/workspaces/{workspace.id}/data?status=DONE"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "DONE"



def test_generate_workspace_summary_runtime_error(db_session: Session, mock_user: Mock):
    user = User(
        username="summary_user",
        email="summary@test.com",
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    workspace = Workspace(
        name="Summary Workspace",
        created_by=user.id,
        invite_code="summary123",
        invite_link="summary-link",
    )
    db_session.add(workspace)
    db_session.flush()

    db_session.add(
        WorkspaceMember(
            user_id=user.id,
            workspace_id=workspace.id,
            role="owner",
        )
    )
    db_session.commit()

    mock_user.id = user.id

    with patch(
        "routes.workspaces.generate_workspace_summary",
        side_effect=RuntimeError("Gemini API unavailable"),
    ):
        response = client.post(
            f"/workspaces/{workspace.id}/summary"
        )

    assert response.status_code == 502
    assert (
        response.json()["detail"]
        == "Failed to generate workspace summary"
    )
