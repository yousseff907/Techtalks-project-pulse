from datetime import datetime

from sqlalchemy.orm import Session

from services.jira_service import JiraService
from models.workspace_data import WorkspaceData
from models.workspace_integration import WorkspaceIntegrations


def gather_and_store_jira_users(integration_id: int, db: Session) -> int:
    integration = (
        db.query(WorkspaceIntegrations)
        .filter(WorkspaceIntegrations.workspace_id == integration_id)
        .first()
    )

    if not integration:
        raise ValueError("Jira integration not found")

    jira_service = JiraService(
        integration.jira_base_url,
        integration.jira_admin_email,
        integration.jira_api_key,
    )

    users = jira_service.fetch_users()

    for user in users:
        normalized_user = {
            "id": user.get("accountId"),
            "name": user.get("displayName"),
            "email": user.get("emailAddress"),
            "active": user.get("active"),
        }

        db.add(
            WorkspaceData(
                integration_id=integration_id,
                type="user",
                source="jira",
                payload=normalized_user,
                fetched_at=datetime.utcnow(),
            )
        )

    db.flush()

    return len(users)