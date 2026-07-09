import jwt
from config import JWT_SECRET
from datetime import datetime, timedelta, timezone

def create_jwt_token(user_id: int, email: str) -> str:
	payload = {"uid": user_id, "email": email, "exp": datetime.now(timezone.utc) + timedelta(days=90)}
	token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
	return token

def verify_jwt_token(token: str) -> dict | None:
	try:
		payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
		return payload
	except jwt.ExpiredSignatureError:
		return None
	except jwt.InvalidTokenError:
		return None