from unittest.mock import patch

from models.workspace import Workspace
from models.workspace_data import WorkspaceData
from models.workspace_integration import WorkspaceIntegrations
from services.sync.notion_sync import gather_and_store_notion_tasks

from utils.encryption import encrypt


def make_workspace_with_integration(db_session, notion_api_key="test-notion-token", invite_code="notiontasktest"):
	workspace = Workspace(
		name="Notion Tasks Sync WS",
		created_by=None,
		invite_code=invite_code,
		invite_link=f"link_{invite_code}",
	)
	db_session.add(workspace)
	db_session.flush()

	integration = WorkspaceIntegrations(
		workspace_id=workspace.id,
		notion_api_key=encrypt(notion_api_key) if notion_api_key else None,
	)
	db_session.add(integration)
	db_session.commit()

	return workspace, integration


def make_notion_task(
	task_id="task-1",
	title="Fix login bug",
	description="Users cannot log in",
	status="In progress",
	priority="High",
	assignee_name="Jane Doe",
	created_time="2026-06-22T14:30:00.000Z",
	last_edited_time="2026-06-23T09:00:00.000Z",
	due_date="2026-07-01",
	tags=None,
):
	return {
		"id": task_id,
		"properties": {
			"Name": {"title": [{"plain_text": title}]} if title else {"title": []},
			"Description": {"rich_text": [{"plain_text": description}]} if description else {"rich_text": []},
			"Status": {"select": {"name": status}} if status else {"select": None},
			"Priority": {"select": {"name": priority}} if priority else {"select": None},
			"Assignee": {"people": [{"name": assignee_name}]} if assignee_name else {"people": []},
			"Due": {"date": {"start": due_date}} if due_date else {"date": None},
			"Tags": {"multi_select": [{"name": t} for t in tags]} if tags else {"multi_select": []},
		},
		"created_time": created_time,
		"last_edited_time": last_edited_time,
	}


# Guard clause tests

def test_returns_zero_when_integration_not_found(db_session):
	result = gather_and_store_notion_tasks(integration_id=999999, db=db_session)

	assert result == 0
	assert db_session.query(WorkspaceData).count() == 0


def test_returns_zero_when_notion_api_key_is_none(db_session):
	workspace, integration = make_workspace_with_integration(db_session, notion_api_key=None, invite_code="notiontasknokey")

	result = gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	assert result == 0
	assert db_session.query(WorkspaceData).filter(WorkspaceData.integration_id == workspace.id).count() == 0


def test_returns_zero_when_no_databases_exist(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontasknodbs")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = []

		result = gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	assert result == 0


def test_returns_zero_when_database_has_no_tasks(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontasknotasks")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "Empty DB"}]
		MockService.return_value.fetch_tasks.return_value = []

		result = gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	assert result == 0


def test_skips_database_with_missing_id(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontasknoid")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "", "title": "Bad DB"}]

		result = gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	assert result == 0
	MockService.return_value.fetch_tasks.assert_not_called()


# Count / multi-database tests

def test_returns_correct_count_across_multiple_databases(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontaskmultidb")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [
			{"id": "db-1", "title": "Sprint Tasks"},
			{"id": "db-2", "title": "Bug Reports"},
		]
		MockService.return_value.fetch_tasks.side_effect = [
			[make_notion_task(task_id="task-1"), make_notion_task(task_id="task-2")],
			[make_notion_task(task_id="task-3")],
		]

		result = gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	assert result == 3


def test_fetch_tasks_called_with_correct_database_id(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontaskdbid")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-42", "title": "Some DB"}]
		MockService.return_value.fetch_tasks.return_value = []

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	MockService.return_value.fetch_tasks.assert_called_once_with(database_id="db-42")


# Field extraction tests

def test_workspace_data_rows_have_correct_fixed_fields(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontaskfixed")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "Sprint Tasks"}]
		MockService.return_value.fetch_tasks.return_value = [make_notion_task()]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row is not None
	assert row.type == "task"
	assert row.source == "notion"
	assert row.integration_id == workspace.id


def test_title_extracted_correctly(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontasktitle")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "DB"}]
		MockService.return_value.fetch_tasks.return_value = [make_notion_task(title="Fix login bug")]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row.title == "Fix login bug"
	assert row.payload["title"] == "Fix login bug"


def test_missing_title_returns_empty_string(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontasknotitle")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "DB"}]
		MockService.return_value.fetch_tasks.return_value = [make_notion_task(title=None)]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row.title == ""
	assert row.payload["title"] == ""


def test_description_extracted_correctly(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontaskdesc")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "DB"}]
		MockService.return_value.fetch_tasks.return_value = [make_notion_task(description="Users cannot log in")]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row.payload["description"] == "Users cannot log in"


def test_priority_extracted_correctly(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontaskpriority")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "DB"}]
		MockService.return_value.fetch_tasks.return_value = [make_notion_task(priority="High")]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row.payload["priority"] == "High"


def test_missing_priority_returns_empty_string(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontasknopriority")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "DB"}]
		MockService.return_value.fetch_tasks.return_value = [make_notion_task(priority=None)]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row.payload["priority"] == ""


def test_assignee_extracted_correctly(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontaskassignee")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "DB"}]
		MockService.return_value.fetch_tasks.return_value = [make_notion_task(assignee_name="Jane Doe")]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row.payload["assignee"] == "Jane Doe"


def test_missing_assignee_returns_empty_string(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontasknoassignee")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "DB"}]
		MockService.return_value.fetch_tasks.return_value = [make_notion_task(assignee_name=None)]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row.payload["assignee"] == ""


def test_tags_extracted_correctly(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontasktags")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "DB"}]
		MockService.return_value.fetch_tasks.return_value = [make_notion_task(tags=["urgent", "backend"])]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row.payload["tags"] == ["urgent", "backend"]


def test_missing_tags_returns_empty_list(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontasknotags")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "DB"}]
		MockService.return_value.fetch_tasks.return_value = [make_notion_task(tags=None)]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row.payload["tags"] == []


def test_missing_due_date_returns_empty_string(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontasknodue")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "DB"}]
		MockService.return_value.fetch_tasks.return_value = [make_notion_task(due_date=None)]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row.payload["due_date"] == ""


# Status normalization tests

def test_status_not_started_normalizes_to_todo(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontaskstatustodo")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "DB"}]
		MockService.return_value.fetch_tasks.return_value = [make_notion_task(status="Not started")]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row.status == "TODO"
	assert row.payload["status"] == "TODO"


def test_status_in_progress_normalizes_to_in_progress(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontaskstatusprog")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "DB"}]
		MockService.return_value.fetch_tasks.return_value = [make_notion_task(status="In progress")]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row.status == "IN_PROGRESS"


def test_status_done_normalizes_to_done(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontaskstatusdone")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "DB"}]
		MockService.return_value.fetch_tasks.return_value = [make_notion_task(status="Done")]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row.status == "DONE"


def test_status_complete_normalizes_to_done(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontaskstatuscomplete")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "DB"}]
		MockService.return_value.fetch_tasks.return_value = [make_notion_task(status="Complete")]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row.status == "DONE"


def test_unrecognized_status_passes_through_unchanged(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontaskstatusweird")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "DB"}]
		MockService.return_value.fetch_tasks.return_value = [make_notion_task(status="Blocked")]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row.status == "Blocked"


def test_missing_status_normalizes_gracefully(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontaskstatusmissing")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "DB"}]
		MockService.return_value.fetch_tasks.return_value = [make_notion_task(status=None)]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row.status == ""


# Date conversion tests

def test_created_at_converted_to_iso8601(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontaskcreatedat")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "DB"}]
		MockService.return_value.fetch_tasks.return_value = [
			make_notion_task(created_time="2026-06-22T14:30:00.000Z")
		]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row.payload["created_at"].startswith("2026-06-22T14:30:00")


def test_due_date_only_string_converted_correctly(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontaskduedateonly")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "DB"}]
		MockService.return_value.fetch_tasks.return_value = [make_notion_task(due_date="2026-07-01")]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row.payload["due_date"] == "2026-07-01"


# fetched_at test

def test_fetched_at_is_timezone_aware(db_session):
	workspace, integration = make_workspace_with_integration(db_session, invite_code="notiontaskfetchedat")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = [{"id": "db-1", "title": "DB"}]
		MockService.return_value.fetch_tasks.return_value = [make_notion_task()]

		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	db_session.commit()

	row = db_session.query(WorkspaceData).filter(
		WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "task"
	).first()

	assert row is not None
	assert row.fetched_at.tzinfo is not None


def test_notion_service_instantiated_with_correct_token(db_session):
	workspace, integration = make_workspace_with_integration(db_session, notion_api_key="secret-task-token", invite_code="notiontasktoken")

	with patch("services.sync.notion_sync.NotionService") as MockService:
		MockService.return_value.fetch_databases.return_value = []
		gather_and_store_notion_tasks(integration_id=workspace.id, db=db_session)

	MockService.assert_called_once_with(api_token="secret-task-token")