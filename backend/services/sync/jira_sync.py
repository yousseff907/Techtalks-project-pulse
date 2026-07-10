import datetime

from sqlalchemy.orm import Session

from utils.encryption import decrypt
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

    if not integration.jira_api_key:
        raise ValueError("Jira API key not found")

    jira_service = JiraService(
        integration.jira_base_url,
        integration.jira_admin_email,
        decrypt(integration.jira_api_key),
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
            )
        )

    db.flush()

    return len(users)


def gather_and_store_jira_projects(integration_id: int, db: Session) -> int:
    integration = (
        db.query(WorkspaceIntegrations)
        .filter(WorkspaceIntegrations.workspace_id == integration_id)
        .first()
    )

    if not integration:
        raise ValueError("Jira integration not found")

    if not integration.jira_api_key:
        raise ValueError("Jira API key not found")

    jira_service = JiraService(
        integration.jira_base_url,
        integration.jira_admin_email,
        decrypt(integration.jira_api_key),
    )

    projects = jira_service.fetch_projects()

    for project in projects:
        normalized_project = {
            "id": project.get("id"),
            "key": project.get("key"),
            "name": project.get("name"),
            "type": project.get("projectTypeKey"),
        }

        db.add(
            WorkspaceData(
                integration_id=integration_id,
                type="project",
                source="jira",
                title=normalized_project["name"],
                payload=normalized_project,
            )
        )

    db.flush()

    return len(projects)

def normalize_jira_status(status: str | None) -> str | None:
    if not status:
        return None

    status = status.lower()

    if status in ["to do", "open"]:
        return "TODO"

    if status in ["in progress", "under review", "testing"]:
        return "IN_PROGRESS"

    if status in ["done", "closed", "resolved"]:
        return "DONE"

    return status.upper()


def convert_date_to_iso(date_value):
    if not date_value:
        return None

    try:
        return datetime.fromisoformat(
            date_value.replace("Z", "+00:00")
        ).isoformat()
    except ValueError:
        return date_value


def gather_and_store_jira_tasks(integration_id: int, db: Session) -> int:
    integration = (
        db.query(WorkspaceIntegrations)
        .filter(WorkspaceIntegrations.workspace_id == integration_id)
        .first()
    )

    if not integration:
        raise ValueError("Jira integration not found")

    if not integration.jira_api_key:
        raise ValueError("Jira API key not found")

    jira_service = JiraService(
        integration.jira_base_url,
        integration.jira_admin_email,
        decrypt(integration.jira_api_key),
    )

    issues = jira_service.fetch_issues()

    for issue in issues:
        fields = issue.get("fields", {})

        status = normalize_jira_status(
            fields.get("status", {}).get("name")
        )

        assignee = fields.get("assignee")
        reporter = fields.get("reporter")
        project = fields.get("project")

        normalized_task = {
            "id": issue.get("id"),
            "key": issue.get("key"),
            "title": fields.get("summary"),
            "description": fields.get("description"),
            "status": status,
            "priority": (
                fields.get("priority", {}).get("name")
                if fields.get("priority")
                else None
            ),
            "assignee": (
                assignee.get("displayName")
                if assignee
                else None
            ),
            "reporter": (
                reporter.get("displayName")
                if reporter
                else None
            ),
            "project": (
                project.get("key")
                if project
                else None
            ),
            "created_at": convert_date_to_iso(
                fields.get("created")
            ),
            "updated_at": convert_date_to_iso(
                fields.get("updated")
            ),
            "due_date": convert_date_to_iso(
                fields.get("duedate")
            ),
        }

        db.add(
            WorkspaceData(
                integration_id=integration_id,
                type="task",
                source="jira",
                title=normalized_task["title"],
                status=normalized_task["status"],
                payload=normalized_task,
            )
        )

    db.flush()

    return len(issues)