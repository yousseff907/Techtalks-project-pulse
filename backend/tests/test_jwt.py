from utils.jwt_helper import create_jwt_token, verify_jwt_token

def test_create_jwt_token_returns_string():
    token = create_jwt_token(1, "test@example.com")
    assert isinstance(token, str)

def test_verify_jwt_token_returns_correct_payload():
    token = create_jwt_token(1, "test@example.com")
    payload = verify_jwt_token(token)
    assert payload["uid"] == 1
    assert payload["email"] == "test@example.com"

def test_verify_jwt_token_invalid_token_returns_none():
    result = verify_jwt_token("invalidtoken")
    assert result is None

def test_verify_jwt_token_expired_token_returns_none():
    from datetime import datetime, timezone, timedelta
    import jwt
    from config import JWT_SECRET
    payload = {"uid": 1, "email": "test@example.com", "exp": datetime.now(timezone.utc) - timedelta(days=1)}
    expired_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    result = verify_jwt_token(expired_token)
    assert result is None