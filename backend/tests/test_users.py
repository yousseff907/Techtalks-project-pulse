from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app import app
from models.workspace import Workspace
from models.workspace_member import WorkspaceMember
from models.user import User
from models.email_rate_limit import EmailRateLimit
from models.verification import Verification
from models.workspace_integration import WorkspaceIntegrations
from models.workspace_data import WorkspaceData

client = TestClient(app)


#Get Current User Profile

def test_get_current_user_profile_success(db_session, mock_user):
    user = User(username="profileuser", email="profile@example.com", is_verified=True)
    db_session.add(user)
    db_session.commit()

    mock_user.id = user.id
    mock_user.username = user.username
    mock_user.email = user.email
    mock_user.is_verified = user.is_verified
    mock_user.created_at = user.created_at

    response = client.get("/users/me")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == user.id
    assert body["username"] == "profileuser"
    assert body["email"] == "profile@example.com"
    assert body["is_verified"] is True
    assert body["created_at"] is not None


def test_get_current_user_profile_unauthenticated(db_session):
    # No mock_user fixture → get_current_user runs for real and rejects
    response = client.get("/users/me")

    assert response.status_code in (401, 403)

#Account Deletion

def test_delete_account_success_no_workspaces(db_session, mock_user):
    user = User(username="deluser", email="deluser@example.com", is_verified=True)
    db_session.add(user)
    db_session.flush()

    user_id = user.id

    mock_user.id = user.id
    mock_user.email = user.email

    owner = User(username="ws_owner", email="owner@example.com")
    db_session.add(owner)
    db_session.flush()

    workspace = Workspace(name="Shared Workspace", created_by=owner.id, invite_code="xyz123", invite_link="xyz.example")
    db_session.add(workspace)
    db_session.flush()

    member = WorkspaceMember(user_id=user.id, workspace_id=workspace.id, role="member")
    v = Verification(user_id=user.id, email=user.email, code="123456")
    rl = EmailRateLimit(user_id=user.id, email=user.email, sent_emails=1)

    db_session.add_all([member, v, rl])
    db_session.commit()

    response = client.delete("/users/me")
    assert response.status_code == 200
    assert response.json()["message"] == "Account deleted successfully"

    assert db_session.query(User).filter(User.id == user_id).first() is None
    assert db_session.query(Verification).filter(Verification.user_id == user_id).first() is None
    assert db_session.query(EmailRateLimit).filter(EmailRateLimit.user_id == user_id).first() is None
    assert db_session.query(WorkspaceMember).filter(WorkspaceMember.user_id == user_id, WorkspaceMember.workspace_id == workspace.id).first() is None


def test_delete_account_failed_workspace_has_no_admin(db_session, mock_user):
    owner = User(username="owner", email="owner@example.com")
    member = User(username="member", email="member@example.com")
    db_session.add_all([owner, member])
    db_session.flush()

    workspace = Workspace(name="WS", created_by=owner.id, invite_code="123", invite_link="x")
    db_session.add(workspace)
    db_session.flush()

    db_session.add(WorkspaceMember(user_id=owner.id, workspace_id=workspace.id, role="owner"))
    db_session.add(WorkspaceMember(user_id=member.id, workspace_id=workspace.id, role="member"))
    db_session.commit()

    mock_user.id = owner.id
    response = client.delete("/users/me")
    assert response.status_code == 400


def test_delete_account_success_transfers_ownership_to_oldest_admin(db_session, mock_user):
    owner = User(username="workspaceowner", email="wsowner@example.com", is_verified=True)
    admin_old = User(username="oldadmin", email="oldadmin@example.com", is_verified=True)
    admin_new = User(username="newadmin", email="newadmin@example.com", is_verified=True)
    db_session.add_all([owner, admin_old, admin_new])
    db_session.flush()

    owner_id = owner.id

    mock_user.id = owner.id
    mock_user.email = owner.email

    ws = Workspace(name="Transfer Target WS", created_by=owner.id, invite_code="code_tx", invite_link="link_tx")
    db_session.add(ws)
    db_session.flush()

    now = datetime.now(timezone.utc)
    m_owner = WorkspaceMember(user_id=owner.id, workspace_id=ws.id, role="owner", joined_at=now - timedelta(days=2))
    m_admin_old = WorkspaceMember(user_id=admin_old.id, workspace_id=ws.id, role="admin", joined_at=now - timedelta(hours=5))
    m_admin_new = WorkspaceMember(user_id=admin_new.id, workspace_id=ws.id, role="admin", joined_at=now - timedelta(hours=1))

    db_session.add_all([m_owner, m_admin_old, m_admin_new])
    db_session.commit()

    response = client.delete("/users/me")
    assert response.status_code == 200
    assert response.json()["message"] == "Account deleted successfully"

    db_session.refresh(ws)
    assert ws.created_by == admin_old.id

    assert db_session.query(User).filter(User.id == owner_id).first() is None
    assert db_session.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == ws.id, WorkspaceMember.user_id == owner_id).first() is None
    assert db_session.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == ws.id, WorkspaceMember.user_id == admin_old.id).first() is not None


def test_delete_account_sole_member_workspace_deleted(db_session, mock_user):
    user = User(username="sole_acc_owner", email="sole_acc@example.com", is_verified=True)
    db_session.add(user)
    db_session.flush()

    user_id = user.id

    workspace = Workspace(name="Solo Account WS", created_by=user_id, invite_code="acc_solo", invite_link="link_acc_solo")
    db_session.add(workspace)
    db_session.flush()
    workspace_id = workspace.id

    member = WorkspaceMember(user_id=user_id, workspace_id=workspace_id, role="owner")
    integration = WorkspaceIntegrations(workspace_id=workspace_id)
    db_session.add_all([member, integration])
    db_session.flush()

    data_row = WorkspaceData(integration_id=workspace_id, type="task", source="jira", title="Task Clean")
    db_session.add(data_row)
    db_session.commit()

    mock_user.id = user_id
    response = client.delete("/users/me")
    assert response.status_code == 200
    assert response.json()["message"] == "Account deleted successfully"

    assert db_session.query(User).filter(User.id == user_id).first() is None
    assert db_session.query(Workspace).filter(Workspace.id == workspace_id).first() is None
    assert db_session.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id).first() is None
    assert db_session.query(WorkspaceIntegrations).filter(WorkspaceIntegrations.workspace_id == workspace_id).first() is None
    assert db_session.query(WorkspaceData).filter(WorkspaceData.integration_id == workspace_id).first() is None


def test_delete_account_rollback_on_failure(db_session, mock_user):
    user = User(username="rb_owner", email="rb_owner@example.com", is_verified=True)
    other_user = User(username="stranded_member", email="stranded@example.com", is_verified=True)
    db_session.add_all([user, other_user])
    db_session.flush()

    ws_solo = Workspace(name="Surviving Solo WS", created_by=user.id, invite_code="rb_solo", invite_link="link_rb_solo")
    db_session.add(ws_solo)
    db_session.flush()
    db_session.add(WorkspaceMember(user_id=user.id, workspace_id=ws_solo.id, role="owner"))
    db_session.add(WorkspaceIntegrations(workspace_id=ws_solo.id))

    ws_blocked = Workspace(name="Blocked WS", created_by=user.id, invite_code="rb_block", invite_link="link_rb_block")
    db_session.add(ws_blocked)
    db_session.flush()
    db_session.add(WorkspaceMember(user_id=user.id, workspace_id=ws_blocked.id, role="owner"))
    db_session.add(WorkspaceMember(user_id=other_user.id, workspace_id=ws_blocked.id, role="member"))
    db_session.commit()

    mock_user.id = user.id
    response = client.delete("/users/me")

    assert response.status_code == 400
    assert "You own workspaces with no admin" in response.json()["detail"]

    assert db_session.query(Workspace).filter(Workspace.id == ws_solo.id).first() is not None
    assert db_session.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == ws_solo.id).first() is not None
    assert db_session.query(WorkspaceIntegrations).filter(WorkspaceIntegrations.workspace_id == ws_solo.id).first() is not None
    assert db_session.query(User).filter(User.id == user.id).first() is not None


#Change Username

def test_update_username_success(db_session, mock_user):
    user = User(username="oldname", email="uname@example.com", is_verified=True)
    db_session.add(user)
    db_session.commit()

    mock_user.id = user.id

    response = client.patch("/users/me", json={"username": "newname"})

    assert response.status_code == 200
    assert response.json() == {"id": user.id, "username": "newname"}

    db_session.refresh(user)
    assert user.username == "newname"


def test_update_username_strips_whitespace(db_session, mock_user):
    user = User(username="oldname", email="trim@example.com", is_verified=True)
    db_session.add(user)
    db_session.commit()

    mock_user.id = user.id

    response = client.patch("/users/me", json={"username": "  trimmed_name  "})

    assert response.status_code == 200
    assert response.json()["username"] == "trimmed_name"

    db_session.refresh(user)
    assert user.username == "trimmed_name"


def test_update_username_dangerous_input(db_session, mock_user):
    user = User(username="safename", email="danger@example.com", is_verified=True)
    db_session.add(user)
    db_session.commit()

    mock_user.id = user.id

    response = client.patch("/users/me", json={"username": "<script>alert(1)</script>"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid username, contains dangerous characters"

    db_session.refresh(user)
    assert user.username == "safename"


def test_update_username_blank_input(db_session, mock_user):
    user = User(username="safename", email="blank_uname@example.com", is_verified=True)
    db_session.add(user)
    db_session.commit()

    mock_user.id = user.id

    response = client.patch("/users/me", json={"username": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "Username cannot be blank"

    db_session.refresh(user)
    assert user.username == "safename"


def test_update_username_empty_string(db_session, mock_user):
    user = User(username="safename", email="empty_uname@example.com", is_verified=True)
    db_session.add(user)
    db_session.commit()

    mock_user.id = user.id

    response = client.patch("/users/me", json={"username": ""})

    assert response.status_code == 400
    assert response.json()["detail"] == "Username cannot be blank"


def test_update_username_unauthenticated(db_session):
    # No mock_user fixture → get_current_user dependency is NOT overridden
    response = client.patch("/users/me", json={"username": "hacker"})

    assert response.status_code in (401, 403)