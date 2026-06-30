from unittest.mock import patch
from fastapi.testclient import TestClient
from app import app
from models.user import User
from models.email_rate_limit import EmailRateLimit
from models.verification import Verification

client = TestClient(app)

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