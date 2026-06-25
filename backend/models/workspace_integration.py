from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from utils.database import Base

class WorkspaceIntegrations(Base):
    __tablename__ = "workspace_integrations"

    workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspaces.id"), primary_key=True)

    jira_api_key: Mapped[str | None] = mapped_column(String, nullable=True)
    
    jira_connected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )

    notion_api_key: Mapped[str | None] = mapped_column(String, nullable=True)

    notion_connected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )