from __future__ import annotations


from datetime import datetime, timezone

from sqlalchemy import String, ForeignKey, DateTime, Boolean, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utils.database import Base 


class Verification(Base):
    __tablename__ = "verifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    
    user: Mapped["User"] = relationship(back_populates="verifications")

    __table_args__ = (
        Index("ix_verifications_user_id_used", "user_id", "used"),
    )

