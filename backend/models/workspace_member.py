from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from utils.database import Base

class WorkspaceMember(Base):
	__tablename__ = "workspace_members"

	user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True, index=True)
	workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspaces.id"), primary_key=True)
	role: Mapped[str] = mapped_column(String, nullable=False, server_default="member")
	joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
