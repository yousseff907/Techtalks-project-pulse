from datetime import datetime
from sqlalchemy.orm import Session
from services.jira_service import JiraService
from models.workspace_data import WorkspaceData
from models.workspace_integration import WorkspaceIntegrations


def gather_and_store_jira_users(integration_id: int, db: Session) -> int:


    # 1. Get Jira integration credentials
    integration = (
        db.query(WorkspaceIntegrations)
        .filter(WorkspaceIntegrations.id == integration_id)
        .first()
    )

    if not integration:
        raise ValueError("Jira integration not found")

    # 2. Create Jira service
    jira_service = JiraService(
        base_url=integration.base_url,
        email=integration.email,
        api_token=integration.api_token,
    )

    # 3. Fetch all Jira users (pagination handled inside JiraService)
    raw_users = jira_service.fetch_users()

    stored_count = 0

    # 4. Normalize and store users
    for raw_user in raw_users:
        normalized_user = {
            "id": raw_user.get("accountId"),
            "name": raw_user.get("displayName"),
            "email": raw_user.get("emailAddress"),
            "active": raw_user.get("active"),
        }

        workspace_data = WorkspaceData(
            integration_id=integration_id,
            type="user",
            source="jira",
            payload=normalized_user,
            fetched_at=datetime.utcnow(),
        )

        db.add(workspace_data)
        db.flush()

        stored_count += 1

    # 5. Return number of stored users
    return stored_count