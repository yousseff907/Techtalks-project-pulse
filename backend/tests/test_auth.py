from datetime import datetime, timezone,timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient
from app import app
from models.user import User
from models.email_rate_limit import EmailRateLimit
from models.verification import Verification

client = TestClient(app)

#Registration

@patch("routes.auth.send_email")
def test_successful_registration(mock_send_email, db_session):
    mock_send_email.return_value = True
    response = client.post("/auth/register", json={"email": "noreply@gmail.com", "username": "NoName"})
    assert response.status_code == 201
    assert response.json()["message"] == "Registration successful, please check your email for your verification code"

    user = db_session.query(User).filter(User.email == "noreply@gmail.com").first()
    assert user is not None
    assert user.username == "NoName"

    rate_limit = db_session.query(EmailRateLimit).filter(EmailRateLimit.user_id == user.id).first()
    assert rate_limit is not None
    assert rate_limit.sent_emails == 1

    verification = db_session.query(Verification).filter(Verification.user_id == user.id).first()
    assert verification is not None

def test_register_invalid_email_format(db_session):
    response = client.post("/auth/register", json={
        "email": "not-an-email",
        "username": "newuser"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid Username or Email format"

def test_register_dangerous_input(db_session):
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "<script>alert(1)</script>"
    })
    assert response.status_code == 400

def test_register_duplicate_email(db_session):
    existing_user = User(username="existing", email="taken@example.com")
    db_session.add(existing_user)
    db_session.commit()

    response = client.post("/auth/register", json={
        "email": "taken@example.com",
        "username": "newuser"
    })
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"

@patch("routes.auth.send_email")
def test_register_email_send_failure_rolls_back(mock_send_email, db_session):
    mock_send_email.return_value = False
    response = client.post("/auth/register", json={
        "email": "failuser@example.com",
        "username": "failuser"
    })
    assert response.status_code == 500

    user = db_session.query(User).filter(User.email == "failuser@example.com").first()
    assert user is None


#Login


@patch("routes.auth.send_email")
def test_login_success(mock_send_email, db_session):
    mock_send_email.return_value = True
    user = User(username="loginuser", email="login@example.com")
    db_session.add(user)
    db_session.flush()
    
    rate_limit = EmailRateLimit(user_id=user.id, email=user.email, sent_emails=0, last_code_date=datetime.now(timezone.utc))
    db_session.add(rate_limit)
    db_session.commit()

    response = client.post("/auth/login", json={"email": "login@example.com"})
    assert response.status_code == 200
    assert response.json()["message"] == "Verification code sent"

    db_session.refresh(rate_limit)
    assert rate_limit.sent_emails == 1

def test_login_invalid_email_format(db_session):
    response = client.post("/auth/login", json={"email": "not-a-valid-email"})
    assert response.status_code == 400

def test_login_dangerous_input(db_session):
    response = client.post("/auth/login", json={"email": "test@example.com; DROP TABLE users;"})
    assert response.status_code == 400

def test_login_email_not_found(db_session):
    response = client.post("/auth/login", json={"email": "missing@example.com"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Email not found"

def test_login_too_many_attempts_block(db_session):
    user = User(username="blockeduser", email="blocked@example.com")
    db_session.add(user)
    db_session.flush()
    
    rate_limit = EmailRateLimit(user_id=user.id, email=user.email, sent_emails=0, last_code_date=datetime.now(timezone.utc))
    db_session.add(rate_limit)
    
    verification = Verification(
        user_id=user.id, 
        email=user.email, 
        code="111111", 
        attempts=5, 
        used=False,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
    )
    db_session.add(verification)
    db_session.commit()

    response = client.post("/auth/login", json={"email": "blocked@example.com"})
    assert response.status_code == 429
    assert "Too many attempts, please retry in" in response.json()["detail"]

def test_login_code_already_sent_cooldown(db_session):
    user = User(username="activeuser", email="active@example.com")
    db_session.add(user)
    db_session.flush()
    
    rate_limit = EmailRateLimit(user_id=user.id, email=user.email, sent_emails=0, last_code_date=datetime.now(timezone.utc))
    db_session.add(rate_limit)
    
    verification = Verification(
        user_id=user.id, 
        email=user.email, 
        code="222222", 
        attempts=0, 
        used=False,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
    )
    db_session.add(verification)
    db_session.commit()

    response = client.post("/auth/login", json={"email": "active@example.com"})
    assert response.status_code == 429
    assert response.json()["detail"] == "A code was already sent, please wait until it expires to request a new one"

def test_login_daily_limit_reached(db_session):
    user = User(username="maxeduser", email="maxed@example.com")
    db_session.add(user)
    db_session.flush()
    
    rate_limit = EmailRateLimit(user_id=user.id, email=user.email, sent_emails=3, last_code_date=datetime.now(timezone.utc))
    db_session.add(rate_limit)
    db_session.commit()

    response = client.post("/auth/login", json={"email": "maxed@example.com"})
    assert response.status_code == 429
    assert response.json()["detail"] == "Daily limit reached, please try again tomorrow"

@patch("routes.auth.send_email")
def test_login_rate_limit_resets_on_new_day(mock_send_email, db_session):
    mock_send_email.return_value = True
    user = User(username="resetuser", email="reset@example.com")
    db_session.add(user)
    db_session.flush()
    
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    rate_limit = EmailRateLimit(user_id=user.id, email=user.email, sent_emails=3, last_code_date=yesterday)
    db_session.add(rate_limit)
    db_session.commit()

    response = client.post("/auth/login", json={"email": "reset@example.com"})
    assert response.status_code == 200
    assert response.json()["message"] == "Verification code sent"

    db_session.refresh(rate_limit)
    assert rate_limit.sent_emails == 1


# Verify

def test_verify_success(db_session):
	user = User(username="verifyuser", email="verify@example.com")
	db_session.add(user)
	db_session.flush()

	verification = Verification(
		user_id=user.id,
		email=user.email,
		code="123456",
		attempts=0,
		used=False,
		expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
	)
	db_session.add(verification)
	db_session.commit()

	response = client.post("/auth/verify", json={"email": "verify@example.com", "code": "123456"})
	assert response.status_code == 200
	assert "access_token" in response.json()
	assert response.json()["token_type"] == "bearer"

	db_session.refresh(user)
	assert user.is_verified

def test_verify_invalid_email_format(db_session):
	response = client.post("/auth/verify", json={"email": "not-an-email", "code": "123456"})
	assert response.status_code == 400
	assert response.json()["detail"] == "Invalid Username or Email format"

def test_verify_dangerous_input(db_session):
	response = client.post("/auth/verify", json={"email": "<script>alert(1)</script>", "code": "123456"})
	assert response.status_code == 400

def test_verify_user_not_found(db_session):
	response = client.post("/auth/verify", json={"email": "ghost@example.com", "code": "123456"})
	assert response.status_code == 404
	assert response.json()["detail"] == "User not found"

def test_verify_no_active_code(db_session):
	user = User(username="nocoduser", email="nocode@example.com")
	db_session.add(user)
	db_session.commit()

	response = client.post("/auth/verify", json={"email": "nocode@example.com", "code": "123456"})
	assert response.status_code == 404
	assert response.json()["detail"] == "No active verification code found, please request a new code"

def test_verify_expired_code(db_session):
	user = User(username="expireduser", email="expired@example.com")
	db_session.add(user)
	db_session.flush()

	verification = Verification(
		user_id=user.id,
		email=user.email,
		code="123456",
		attempts=0,
		used=False,
		expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)
	)
	db_session.add(verification)
	db_session.commit()

	response = client.post("/auth/verify", json={"email": "expired@example.com", "code": "123456"})
	assert response.status_code == 404
	assert response.json()["detail"] == "No active verification code found, please request a new code"

def test_verify_too_many_attempts(db_session):
	user = User(username="blockeduser", email="blocked@example.com")
	db_session.add(user)
	db_session.flush()

	verification = Verification(
		user_id=user.id,
		email=user.email,
		code="123456",
		attempts=4,
		used=False,
		expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
	)
	db_session.add(verification)
	db_session.commit()

	response = client.post("/auth/verify", json={"email": "blocked@example.com", "code": "wrong"})
	assert response.status_code == 429
	assert response.json()["detail"] == "Too many attempts, please request a new code"

def test_verify_wrong_code(db_session):
	user = User(username="wronguser", email="wrong@example.com")
	db_session.add(user)
	db_session.flush()

	verification = Verification(
		user_id=user.id,
		email=user.email,
		code="123456",
		attempts=0,
		used=False,
		expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
	)
	db_session.add(verification)
	db_session.commit()

	response = client.post("/auth/verify", json={"email": "wrong@example.com", "code": "999999"})
	assert response.status_code == 400
	assert response.json()["detail"] == "Invalid code"

def test_verify_already_used_code(db_session):
	user = User(username="useduser", email="used@example.com")
	db_session.add(user)
	db_session.flush()

	verification = Verification(
		user_id=user.id,
		email=user.email,
		code="123456",
		attempts=0,
		used=True,
		expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
	)
	db_session.add(verification)
	db_session.commit()

	response = client.post("/auth/verify", json={"email": "used@example.com", "code": "123456"})
	assert response.status_code == 404
	assert response.json()["detail"] == "No active verification code found, please request a new code"


# Entire Auth flow

@patch("routes.auth.send_email")
def test_full_auth_flow(mock_send_email, db_session):
	mock_send_email.return_value = True

	# Register
	response = client.post("/auth/register", json={"email": "fullflow@example.com", "username": "flowuser"})
	assert response.status_code == 201

	# Get the verification code from DB
	user = db_session.query(User).filter(User.email == "fullflow@example.com").first()
	assert user is not None
	verification = db_session.query(Verification).filter(Verification.user_id == user.id).first()
	assert verification is not None

	# Verify
	response = client.post("/auth/verify", json={"email": "fullflow@example.com", "code": verification.code})
	assert response.status_code == 200
	assert "access_token" in response.json()

	db_session.refresh(user)
	assert user.is_verified

	# Login
	response = client.post("/auth/login", json={"email": "fullflow@example.com"})
	assert response.status_code == 200
	assert response.json()["message"] == "Verification code sent"

	# Get new verification code and verify again
	db_session.expire(user)
	new_verification = db_session.query(Verification).filter(
		Verification.user_id == user.id,
		Verification.used.is_(False)
	).first()
	assert new_verification is not None

	response = client.post("/auth/verify", json={"email": "fullflow@example.com", "code": new_verification.code})
	assert response.status_code == 200
	assert "access_token" in response.json()



# Account Deletion

#Cascade deletion test
def test_delete_account_success_no_workspaces(db_session, mock_user):
    user = User(username="deluser", email="deluser@example.com", is_verified=True)
    db_session.add(user)
    db_session.flush()
    
    user_id = user.id
    
    mock_user.id = user.id
    mock_user.email = user.email

    v = Verification(user_id=user.id, email=user.email, code="123456")
    rl = EmailRateLimit(user_id=user.id, email=user.email, sent_emails=1)
    db_session.add_all([v, rl])
    db_session.commit()

    response = client.delete("/auth/me")
    assert response.status_code == 200
    assert response.json()["message"] == "Account deleted successfully"

    assert db_session.query(User).filter(User.id == user_id).first() is None
    assert db_session.query(Verification).filter(Verification.user_id == user_id).first() is None
    assert db_session.query(EmailRateLimit).filter(EmailRateLimit.user_id == user_id).first() is None


def test_delete_account_failed_workspace_has_no_admin(db_session, mock_user):
    from models.workspace import Workspace
    from models.workspace_member import WorkspaceMember

    user = User(username="soleowner", email="soleowner@example.com", is_verified=True)
    db_session.add(user)
    db_session.flush()
    
    mock_user.id = user.id
    mock_user.email = user.email

    ws = Workspace(name="No Admin WS", created_by=user.id, invite_code="code_na", invite_link="link_na")
    db_session.add(ws)
    db_session.flush()
    
    member = WorkspaceMember(user_id=user.id, workspace_id=ws.id, role="owner")
    db_session.add(member)
    db_session.commit()

    response = client.delete("/auth/me")
    assert response.status_code == 400
    assert response.json()["detail"] == "You own workspaces with no admin. Please promote a member to admin or delete the workspace before deleting your account"

    assert db_session.query(User).filter(User.id == user.id).first() is not None


def test_delete_account_success_transfers_ownership_to_oldest_admin(db_session, mock_user):
    from models.workspace import Workspace
    from models.workspace_member import WorkspaceMember

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

    response = client.delete("/auth/me")
    assert response.status_code == 200
    assert response.json()["message"] == "Account deleted successfully"

    db_session.refresh(ws)
    assert ws.created_by == admin_old.id
    
    assert db_session.query(User).filter(User.id == owner_id).first() is None
    assert db_session.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == ws.id, WorkspaceMember.user_id == owner_id).first() is None
    
    assert db_session.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == ws.id, WorkspaceMember.user_id == admin_old.id).first() is not None