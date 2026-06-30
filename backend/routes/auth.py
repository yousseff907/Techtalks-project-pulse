from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from utils.validators import is_dangerous, is_valid_email_format
from utils.database import get_db, Session
from models.user import User
from models.email_rate_limit import EmailRateLimit
from models.verification import Verification
from utils.verification import generate_code
from services.email_service import send_email
from sqlalchemy.exc import IntegrityError

router = APIRouter()

class RegisterRequest(BaseModel):
	email: str
	username: str

@router.post("/auth/register", status_code=201)
def	register(request: RegisterRequest, db: Session = Depends(get_db)):
	try:
		if is_dangerous(request.email) or is_dangerous(request.username) or not is_valid_email_format(request.email):
			raise HTTPException(status_code=400, detail="Invalid Username or Email format")

		if db.query(User).filter(User.email == request.email).first() is not None:
			raise HTTPException(status_code=409, detail="Email already registered")

		user = User(username=request.username, email=request.email)
		db.add(user)
		db.flush()

		verification_code = generate_code()
		rate_limit = EmailRateLimit(user=user, user_id=user.id, email=request.email, sent_emails=1)
		db.add(rate_limit)

		is_sent = send_email(request.email, verification_code)
		if not is_sent:
			db.rollback()
			raise HTTPException(status_code=500, detail="Failed to send verification email, try again later")

		verification = Verification(user_id=user.id, code=verification_code, email=request.email)
		db.add(verification)

		db.commit()
		db.refresh(user)
		db.refresh(rate_limit)
		db.refresh(verification)
		
		return {"message": "Registration successful, please check your email for your verification code"}

	except IntegrityError:
		db.rollback()
		raise HTTPException(status_code=409, detail="Email already registered")
