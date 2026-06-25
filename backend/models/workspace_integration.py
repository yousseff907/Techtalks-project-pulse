from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, FetchedValue
from sqlalchemy.orm import Mapped, mapped_column
from utils.database import Base

#Note for Jira and Notion connected at columns: Add trigger to PostgreSQL to update time with FetchedValue()

class WorkspaceIntegrations(Base):
    __tablename__ = "workspace_integrations"

    workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspaces.id"), primary_key=True)

    jira_api_key: Mapped[str | None] = mapped_column(String, nullable=True)
    
    jira_connected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), 
        nullable=True, 
        server_default=FetchedValue()
    )

    notion_api_key: Mapped[str | None] = mapped_column(String, nullable=True)

    notion_connected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), 
        nullable=True, 
        server_default=FetchedValue()
    )