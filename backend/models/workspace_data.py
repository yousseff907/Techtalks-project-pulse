from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from utils.database import Base


class WorkspaceData(Base):
    __tablename__ = "workspace_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    integration_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspace_integrations.workspace_id"), index=True)

    type: Mapped[str] = mapped_column(String, nullable=False)

    source: Mapped[str] = mapped_column(String, nullable=False)

    title: Mapped[str | None] = mapped_column(String, nullable=True)

    status: Mapped[str | None] = mapped_column(String, nullable=True)

    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())