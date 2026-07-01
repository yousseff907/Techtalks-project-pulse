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
def test_succesfull_registration(mock_send_email, db_session):
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