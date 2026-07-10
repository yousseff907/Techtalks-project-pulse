from sqlalchemy.orm import Session

from models.workspace_data import WorkspaceData
from models.workspace_integration import WorkspaceIntegrations
from services.notion_service import NotionService
from utils.encryption import decrypt

def gather_and_store_notion_users(integration_id: int, db: Session) -> int:
    integration = (
        db.query(WorkspaceIntegrations)
        .filter(WorkspaceIntegrations.workspace_id == integration_id)
        .first()
    )

    if integration is None or integration.notion_api_key is None:
        return 0

    service = NotionService(api_token=decrypt(integration.notion_api_key))
    raw_users = service.fetch_users()

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
        ))

    db.flush()
    return len(raw_users)


def gather_and_store_notion_databases(integration_id: int, db: Session) -> int:
    integration = (
        db.query(WorkspaceIntegrations)
        .filter(WorkspaceIntegrations.workspace_id == integration_id)
        .first()
    )

    if integration is None or integration.notion_api_key is None:
        return 0

    service = NotionService(api_token=decrypt(integration.notion_api_key))
    raw_databases = service.fetch_databases()

    for db_record in raw_databases:
        normalized = {
            "id": db_record.get("id", ""),
            "title": db_record.get("title", ""),
        }

        db.add(WorkspaceData(
            integration_id=integration_id,
            type="project",
            source="notion",
            title=normalized["title"],
            payload=normalized,
        ))

    db.flush()
    return len(raw_databases)
