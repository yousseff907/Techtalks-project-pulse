from datetime import datetime, timezone
import math
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from utils.validators import is_dangerous, is_valid_email_format
from utils.database import get_db, Session
from models.user import User
from models.email_rate_limit import EmailRateLimit
from models.verification import Verification
from utils.verification import generate_code
from services.email_service import send_email
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from utils.background_tasks import cleanup_expired_codes
from utils.jwt_helper import create_jwt_token

router = APIRouter()

class RegisterRequest(BaseModel):
	email: str
	username: str

class LoginRequest(BaseModel):
	email: str

class VerifyRequest(BaseModel):
	email: str
	code: str

@router.post("/auth/register", status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
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


@router.post("/auth/login", status_code=200)
def login(request: LoginRequest, db: Session = Depends(get_db)):
		
	#Validate
		
	if is_dangerous(request.email) or not is_valid_email_format(request.email):
		raise HTTPException(status_code=400, detail="Invalid Email format")

	#DB Check
		
	user = db.query(User).filter(User.email == request.email).first()
	if user is None:
		raise HTTPException(status_code=404, detail="Email not found")

	#Attempts >= 5
		
	blocked_verification = db.query(Verification).filter(
		Verification.user_id == user.id,
		Verification.used.is_(False),
		Verification.expires_at > func.now(),
		Verification.attempts >= 5
	).first()

	if blocked_verification:
		remaining_seconds = (blocked_verification.expires_at - datetime.now(timezone.utc)).total_seconds()
		remaining_minutes = math.ceil(remaining_seconds / 60)
		if remaining_minutes < 1:
			remaining_minutes = 1
		raise HTTPException(
			status_code=429, 
			detail=f"Too many attempts, please retry in {remaining_minutes} minutes"
		)

	#Code exists
		
	existing_verification = db.query(Verification).filter(
		Verification.user_id == user.id,
		Verification.used.is_(False),
		Verification.expires_at > func.now()
	).first()

	if existing_verification:
		raise HTTPException(
			status_code=429, 
			detail="A code was already sent, please wait until it expires to request a new one"
		)

	# check rate, if new day, reset
	rate_limit = db.query(EmailRateLimit).filter(EmailRateLimit.user_id == user.id).first()
	if rate_limit:
		if rate_limit.last_code_date.date() != datetime.now(timezone.utc).date():
			rate_limit.sent_emails = 0
			rate_limit.last_code_date = datetime.now(timezone.utc)
			db.flush()

	# check if limit reached (3)
	if rate_limit and rate_limit.sent_emails >= 3:
		raise HTTPException(
			status_code=429, 
			detail="Daily limit reached, please try again tomorrow"
		)

	# Generate code, save to DB, send email
	verification_code = generate_code()
		
	verification = Verification(user_id=user.id, code=verification_code, email=request.email)
	db.add(verification)

	if rate_limit:
		rate_limit.sent_emails += 1
		rate_limit.last_code_date = datetime.now(timezone.utc)
	else:
		rate_limit = EmailRateLimit(user_id=user.id, email=request.email, sent_emails=1, last_code_date=datetime.now(timezone.utc))
		db.add(rate_limit)

	is_sent = send_email(request.email, verification_code)
	if not is_sent:
		db.rollback()
		raise HTTPException(status_code=500, detail="Failed to send verification email, try again later")

	db.commit()
	return {"message": "Verification code sent"}

@router.post("/auth/verify", status_code=200)
def	verify_code(background_task: BackgroundTasks, request: VerifyRequest, db: Session = Depends(get_db)):
	try:
		if is_dangerous(request.email) or not is_valid_email_format(request.email):
			raise HTTPException(status_code=400, detail="Invalid Username or Email format")

		user = db.query(User).filter(User.email == request.email).first()

		if user is None:
			raise HTTPException(status_code=404, detail="User not found")
		
		verification = db.query(Verification).filter(Verification.user_id == user.id, Verification.expires_at > func.now(), Verification.used == False).first()
		if verification is None:
			raise HTTPException(status_code=404, detail="No active verification code found, please request a new code")

		verification.attempts += 1
		db.commit()

		if verification.attempts >= 5:
			raise HTTPException(status_code=429, detail="Too many attempts, please request a new code")
		
		if request.code != verification.code:
			raise HTTPException(status_code=400, detail="Invalid code")

		user.is_verified = True
		verification.used = True

		db.commit()
		jwt_token = create_jwt_token(user.id, user.email)

		background_task.add_task(cleanup_expired_codes, db, user.id)

		return {"access_token": jwt_token, "token_type": "bearer"}

	except IntegrityError:
		db.rollback()
		raise HTTPException(status_code=409, detail="Integrity error")