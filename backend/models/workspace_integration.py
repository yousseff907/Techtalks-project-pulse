from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from utils.database import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from models.workspace import Workspace

class WorkspaceIntegrations(Base):
	__tablename__ = "workspace_integrations"

	workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True, index=True)

	jira_api_key: Mapped[str | None] = mapped_column(String, nullable=True)

	jira_connected_at: Mapped[datetime | None] = mapped_column(
		DateTime(timezone=True), 
		nullable=True
	)

	jira_base_url: Mapped[str | None] = mapped_column(String, nullable=True)

	jira_admin_email: Mapped[str | None] = mapped_column(String, nullable=True)

		

	notion_api_key: Mapped[str | None] = mapped_column(String, nullable=True)

	notion_connected_at: Mapped[datetime | None] = mapped_column(
		DateTime(timezone=True), 
		nullable=True
	)

	workspace: Mapped["Workspace"] = relationship(back_populates="integration", uselist=False)