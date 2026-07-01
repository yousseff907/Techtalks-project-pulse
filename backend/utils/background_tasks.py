from utils.database import Session
from sqlalchemy import or_, func
from models.verification import Verification

def	cleanup_expired_codes(db: Session, user_id: int):
	db.query(Verification).filter(Verification.user_id == user_id, or_ (Verification.expires_at <= func.now(), Verification.used)).delete()
	db.commit()