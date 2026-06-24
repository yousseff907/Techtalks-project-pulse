from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from utils.database import Base


class Workspace(Base):
	__tablename__ = "workspaces"

    #Since implementing in PostgreSQL, no need for auto-incrementing. 
    #PostgreSQL will handle this automatically with the SERIAL type.
	
	id: Mapped[int] = mapped_column(Integer, primary_key=True)
	
	name: Mapped[str] = mapped_column(String(255), nullable=False)
	
	created_at: Mapped[datetime] = mapped_column(
		DateTime,
		server_default=func.now(), #At creation, set it to current time
		nullable=True,
	)
	
	created_by: Mapped[int | None] = mapped_column(
		Integer,
		ForeignKey("users.id", ondelete="SET NULL"),
		nullable=True,
	)
	
	invite_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
	
	invite_link: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
