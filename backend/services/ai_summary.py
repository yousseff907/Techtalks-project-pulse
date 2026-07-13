from collections import Counter
from datetime import datetime, timezone

from google import genai
from sqlalchemy.orm import Session

from config import GEMINI_API_KEY
from models.workspace_data import WorkspaceData
from models.workspace_integration import WorkspaceIntegrations


def generate_workspace_summary(workspace_id: int, db: Session) -> str:
    integration = (
        db.query(WorkspaceIntegrations)
        .filter(
            WorkspaceIntegrations.workspace_id == workspace_id
        )
        .first()
    )

    if integration is None:
        raise ValueError("Workspace integration not found")

    task_rows = (
        db.query(WorkspaceData)
        .filter(
            WorkspaceData.integration_id == integration.workspace_id,
            WorkspaceData.type == "task",
        )
        .all()
    )
    total_tasks = len(task_rows)

    status_counts = Counter()

    overdue_tasks = []
    high_priority_tasks = []

    today = datetime.now(timezone.utc).date()

    for row in task_rows:
        payload = row.payload or {}

        status = payload.get("status", "UNKNOWN")
        status_counts[status] += 1

        priority = (payload.get("priority") or "").strip().lower()

        if priority == "high":
            high_priority_tasks.append(payload.get("title", "Untitled"))

        due_date = payload.get("due_date")

        if due_date:
            try:
                due = datetime.fromisoformat(
                    due_date.replace("Z", "+00:00")
                ).date()

                if due < today and status != "DONE":
                    overdue_tasks.append(
                        payload.get("title", "Untitled")
                    )

            except ValueError:
                pass

    prompt = f"""
You are summarizing the current state of a software project's tasks.

Task Summary

Total tasks: {total_tasks}

Status breakdown:
{chr(10).join(f"- {status}: {count}" for status, count in status_counts.items())}

High priority tasks:
{chr(10).join(f"- {title}" for title in high_priority_tasks) or "- None"}

Overdue tasks:
{chr(10).join(f"- {title}" for title in overdue_tasks) or "- None"}

Write a concise project health summary in 2-4 paragraphs.
Mention overall progress, risks, bottlenecks, and any notable priorities.
"""

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model="gemini-2.5-flash", #Set a default for now, until api later provided
            contents=prompt,
        )

        return response.text

    except Exception as exc:
        raise RuntimeError(
            "Failed to generate workspace summary."
        ) from exc