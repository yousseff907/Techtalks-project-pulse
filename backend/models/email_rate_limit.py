
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utils.database import Base  
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from models.user import User

class EmailRateLimit(Base):
	__tablename__ = "email_rate_limits"

	user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)

	email: Mapped[str] = mapped_column(String, nullable=False)

	last_code_date: Mapped[datetime] = mapped_column( DateTime(timezone=True), nullable=False ,server_default=func.now())

	sent_emails: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

	user: Mapped["User"] = relationship(back_populates="rate_limit", uselist=False)
