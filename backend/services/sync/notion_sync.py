from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.workspace_data import WorkspaceData
from models.workspace_integration import WorkspaceIntegrations
from services.notion_service import NotionService


def gather_and_store_notion_users(integration_id: int, db: Session) -> int:
    integration = (
        db.query(WorkspaceIntegrations)
        .filter(WorkspaceIntegrations.workspace_id == integration_id)
        .first()
    )

    if integration is None or integration.notion_api_key is None:
        return 0

     #Fetch all users via NotionService
    service = NotionService(api_token=integration.notion_api_key)
    raw_users = service.fetch_users()

    #Normalize each user and insert a WorkspaceData row
    for user in raw_users:
        normalized = {
            "id": user.get("id", ""),
            "name": user.get("name", ""),
            "email": user.get("email", ""),
        }

        db.add(WorkspaceData(
            integration_id=integration_id,
            type="user",
            source="notion",
            payload=normalized,
            fetched_at=datetime.now(timezone.utc),
        ))

    db.flush()

    return len(raw_users)