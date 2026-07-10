from datetime import datetime, date,timezone

from sqlalchemy.orm import Session

from models.workspace_data import WorkspaceData
from models.workspace_integration import WorkspaceIntegrations
from services.notion_service import NotionService
from utils.encryption import decrypt


_STATUS_MAP = {
    "not started": "TODO",
    "in progress": "IN_PROGRESS",
    "done": "DONE",
    "complete": "DONE",
}


def _normalize_status(raw_status: str) -> str:
    return _STATUS_MAP.get(raw_status.lower().strip(), raw_status)


def _to_iso8601(date_str: str | None) -> str:
    if not date_str:
        return ""

    try:
        if len(date_str) == 10:
            return date.fromisoformat(date_str).isoformat()

        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.isoformat()

    except ValueError:
        return date_str

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
            fetched_at=datetime.now(timezone.utc),
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
            fetched_at=datetime.now(timezone.utc),
        ))

    db.flush()
    return len(raw_databases)


def gather_and_store_notion_tasks(integration_id: int, db: Session) -> int:
    integration = (
        db.query(WorkspaceIntegrations)
        .filter(WorkspaceIntegrations.workspace_id == integration_id)
        .first()
    )

    if integration is None or integration.notion_api_key is None:
        return 0

    service = NotionService(api_token=decrypt(integration.notion_api_key))
    databases = service.fetch_databases()

    total_tasks = 0

    for database in databases:
        database_id = database.get("id", "")
        if not database_id:
            continue

        raw_tasks = service.fetch_tasks(database_id=database_id)

        for task in raw_tasks:
            props = task.get("properties", {})

            title_arr = props.get("Name", {}).get("title", [])
            title = title_arr[0].get("plain_text", "") if title_arr else ""

            desc_arr = props.get("Description", {}).get("rich_text", [])
            description = desc_arr[0].get("plain_text", "") if desc_arr else ""

            status_select = props.get("Status", {}).get("select") or {}
            raw_status = status_select.get("name", "")
            status = _normalize_status(raw_status)

            priority_select = props.get("Priority", {}).get("select") or {}
            priority = priority_select.get("name", "")

            people = props.get("Assignee", {}).get("people", [])
            assignee = people[0].get("name", "") if people else ""

            created_at = _to_iso8601(task.get("created_time", ""))
            updated_at = _to_iso8601(task.get("last_edited_time", ""))

            due_date_obj = props.get("Due", {}).get("date") or {}
            due_date = _to_iso8601(due_date_obj.get("start", ""))

            tags_arr = props.get("Tags", {}).get("multi_select", [])
            tags = [tag.get("name", "") for tag in tags_arr]

            normalized = {
                "id": task.get("id", ""),
                "title": title,
                "description": description,
                "status": status,
                "priority": priority,
                "assignee": assignee,
                "created_at": created_at,
                "updated_at": updated_at,
                "due_date": due_date,
                "tags": tags,
            }

            db.add(WorkspaceData(
                integration_id=integration_id,
                type="task",
                source="notion",
                title=title,
                status=status,
                payload=normalized,
                fetched_at=datetime.now(timezone.utc),
            ))

            total_tasks += 1

    db.flush()
    return total_tasks