from database import Session
from sqlalchemy import or_, func
from models.verification import Verification
from datetime import datetime, timezone

def	cleanup_expired_codes(db: Session, user_id: int):
	db.query(Verification).filter(Verification.user_id == user_id, or_ (Verification.expires_at <= func.now(), Verification.used == True)).delete()
	db.commit()