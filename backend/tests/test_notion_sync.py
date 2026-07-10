
from unittest.mock import MagicMock, patch

from models.workspace_data import WorkspaceData
from models.workspace_integration import WorkspaceIntegrations
from services.sync.notion_sync import (
    gather_and_store_notion_users,
    gather_and_store_notion_databases,
    gather_and_store_notion_tasks,
    _normalize_status,
    _to_iso8601,
)
from utils.encryption import encrypt


RAW_DATABASES = [
    {"id": "db-1", "title": "Project Tracker"},
    {"id": "db-2", "title": "Bug Reports"},
]

def make_mock_integration(notion_api_key="test-notion-token"):
    integration = MagicMock(spec=WorkspaceIntegrations)
    integration.notion_api_key = encrypt(notion_api_key) if notion_api_key else None
    return integration


def make_mock_db(integration=None):
    mock_db = MagicMock()

    def query_side_effect(model):
        mock_query = MagicMock()
        if model == WorkspaceIntegrations:
            mock_query.filter.return_value.first.return_value = integration
        return mock_query

    mock_db.query.side_effect = query_side_effect
    return mock_db


RAW_USERS = [
    {"id": "user-1", "name": "John Doe", "email": "john@example.com"},
    {"id": "user-2", "name": "Jane Smith", "email": "jane@example.com"},
]


def test_returns_zero_when_integration_not_found():
    mock_db = make_mock_db(integration=None)

    result = gather_and_store_notion_users(integration_id=1, db=mock_db)

    assert result == 0
    mock_db.add.assert_not_called()
    mock_db.flush.assert_not_called()


def test_returns_zero_when_notion_api_key_is_none():
    integration = make_mock_integration(notion_api_key=None)
    mock_db = make_mock_db(integration=integration)

    result = gather_and_store_notion_users(integration_id=1, db=mock_db)

    assert result == 0
    mock_db.add.assert_not_called()
    mock_db.flush.assert_not_called()


def test_returns_zero_when_no_users_returned():
    integration = make_mock_integration()
    mock_db = make_mock_db(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_users.return_value = []

        result = gather_and_store_notion_users(integration_id=1, db=mock_db)

    assert result == 0
    mock_db.add.assert_not_called()
    mock_db.flush.assert_called_once()


def test_returns_correct_count_of_users_stored():
    integration = make_mock_integration()
    mock_db = make_mock_db(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_users.return_value = RAW_USERS

        result = gather_and_store_notion_users(integration_id=1, db=mock_db)

    assert result == 2


def test_inserts_one_row_per_user():
    integration = make_mock_integration()
    mock_db = make_mock_db(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_users.return_value = RAW_USERS

        gather_and_store_notion_users(integration_id=1, db=mock_db)

    assert mock_db.add.call_count == 2


def test_flush_called_once_after_all_inserts():
    integration = make_mock_integration()
    mock_db = make_mock_db(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_users.return_value = RAW_USERS

        gather_and_store_notion_users(integration_id=1, db=mock_db)

    mock_db.flush.assert_called_once()


def test_workspace_data_rows_have_correct_fixed_fields():
    integration = make_mock_integration()
    mock_db = make_mock_db(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_users.return_value = RAW_USERS

        gather_and_store_notion_users(integration_id=42, db=mock_db)

    added_rows = [c.args[0] for c in mock_db.add.call_args_list]

    for row in added_rows:
        assert isinstance(row, WorkspaceData)
        assert row.type == "user"
        assert row.source == "notion"
        assert row.integration_id == 42


def test_workspace_data_payload_contains_normalized_fields():
    integration = make_mock_integration()
    mock_db = make_mock_db(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_users.return_value = RAW_USERS

        gather_and_store_notion_users(integration_id=1, db=mock_db)

    added_rows = [c.args[0] for c in mock_db.add.call_args_list]  # ← call → c

    assert added_rows[0].payload == {
        "id": "user-1",
        "name": "John Doe",
        "email": "john@example.com",
    }
    assert added_rows[1].payload == {
        "id": "user-2",
        "name": "Jane Smith",
        "email": "jane@example.com",
    }


def test_workspace_data_payload_excludes_extra_fields():
    integration = make_mock_integration()
    mock_db = make_mock_db(integration=integration)

    raw_users_with_extra = [
        {
            "id": "user-1",
            "name": "John Doe",
            "email": "john@example.com",
            "active": True,       # should not appear in payload
            "avatar_url": "...",  # should not appear in payload
        }
    ]

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_users.return_value = raw_users_with_extra

        gather_and_store_notion_users(integration_id=1, db=mock_db)

    added_row = mock_db.add.call_args[0][0]
    assert set(added_row.payload.keys()) == {"id", "name", "email"}


def test_workspace_data_fetched_at_is_timezone_aware():
    integration = make_mock_integration()
    mock_db = make_mock_db(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_users.return_value = RAW_USERS[:1]

        gather_and_store_notion_users(integration_id=1, db=mock_db)

    added_row = mock_db.add.call_args[0][0]
    assert added_row.fetched_at.tzinfo is not None


def test_notion_service_instantiated_with_correct_token():
    integration = make_mock_integration(notion_api_key="secret-token-abc")
    mock_db = make_mock_db(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_users.return_value = []
        gather_and_store_notion_users(integration_id=1, db=mock_db)

    MockService.assert_called_once_with(api_token="secret-token-abc")

def make_mock_db_for_databases(integration=None):
    mock_db = MagicMock()

    def query_side_effect(model):
        mock_query = MagicMock()
        if model == WorkspaceIntegrations:
            mock_query.filter.return_value.first.return_value = integration
        return mock_query

    mock_db.query.side_effect = query_side_effect
    return mock_db


def test_databases_returns_zero_when_integration_not_found():
    mock_db = make_mock_db_for_databases(integration=None)

    result = gather_and_store_notion_databases(integration_id=1, db=mock_db)

    assert result == 0
    mock_db.add.assert_not_called()
    mock_db.flush.assert_not_called()


def test_databases_returns_zero_when_notion_api_key_is_none():
    integration = make_mock_integration(notion_api_key=None)
    mock_db = make_mock_db_for_databases(integration=integration)

    result = gather_and_store_notion_databases(integration_id=1, db=mock_db)

    assert result == 0
    mock_db.add.assert_not_called()
    mock_db.flush.assert_not_called()


def test_databases_returns_zero_when_no_databases_returned():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_databases(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = []

        result = gather_and_store_notion_databases(integration_id=1, db=mock_db)

    assert result == 0
    mock_db.add.assert_not_called()
    mock_db.flush.assert_called_once()


def test_databases_returns_correct_count():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_databases(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES

        result = gather_and_store_notion_databases(integration_id=1, db=mock_db)

    assert result == 2


def test_databases_inserts_one_row_per_database():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_databases(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES

        gather_and_store_notion_databases(integration_id=1, db=mock_db)

    assert mock_db.add.call_count == 2


def test_databases_flush_called_once_after_all_inserts():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_databases(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES

        gather_and_store_notion_databases(integration_id=1, db=mock_db)

    mock_db.flush.assert_called_once()


def test_databases_rows_have_correct_fixed_fields():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_databases(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES

        gather_and_store_notion_databases(integration_id=42, db=mock_db)

    added_rows = [c.args[0] for c in mock_db.add.call_args_list]

    for row in added_rows:
        assert isinstance(row, WorkspaceData)
        assert row.type == "project"
        assert row.source == "notion"
        assert row.integration_id == 42


def test_databases_title_is_set_on_row():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_databases(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES

        gather_and_store_notion_databases(integration_id=1, db=mock_db)

    added_rows = [c.args[0] for c in mock_db.add.call_args_list]

    assert added_rows[0].title == "Project Tracker"
    assert added_rows[1].title == "Bug Reports"


def test_databases_payload_contains_normalized_fields():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_databases(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES

        gather_and_store_notion_databases(integration_id=1, db=mock_db)

    added_rows = [c.args[0] for c in mock_db.add.call_args_list]

    assert added_rows[0].payload == {"id": "db-1", "title": "Project Tracker"}
    assert added_rows[1].payload == {"id": "db-2", "title": "Bug Reports"}


def test_databases_payload_excludes_extra_fields():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_databases(integration=integration)

    raw_databases_with_extra = [
        {
            "id": "db-1",
            "title": "Project Tracker",
            "created_time": "2024-01-01",  # should not appear in payload
            "object": "database",           # should not appear in payload
        }
    ]

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = raw_databases_with_extra

        gather_and_store_notion_databases(integration_id=1, db=mock_db)

    added_row = mock_db.add.call_args[0][0]
    assert set(added_row.payload.keys()) == {"id", "title"}


def test_databases_fetched_at_is_timezone_aware():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_databases(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES[:1]

        gather_and_store_notion_databases(integration_id=1, db=mock_db)

    added_row = mock_db.add.call_args[0][0]
    assert added_row.fetched_at.tzinfo is not None


def test_databases_notion_service_instantiated_with_correct_token():
    integration = make_mock_integration(notion_api_key="secret-db-token")
    mock_db = make_mock_db_for_databases(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = []
        gather_and_store_notion_databases(integration_id=1, db=mock_db)

    MockService.assert_called_once_with(api_token="secret-db-token")

def make_mock_db_for_tasks(integration=None):
    mock_db = MagicMock()

    def query_side_effect(model):
        mock_query = MagicMock()
        if model == WorkspaceIntegrations:
            mock_query.filter.return_value.first.return_value = integration
        return mock_query

    mock_db.query.side_effect = query_side_effect
    return mock_db


def make_raw_task(
    task_id="task-1",
    title="Fix bug",
    description="Something broke",
    status="In progress",
    priority="High",
    assignee_name="John Doe",
    created_time="2024-01-01T00:00:00.000Z",
    last_edited_time="2024-01-02T00:00:00.000Z",
    due_date="2024-01-15",
    tags=None,
):
    return {
        "id": task_id,
        "created_time": created_time,
        "last_edited_time": last_edited_time,
        "properties": {
            "Name": {"title": [{"plain_text": title}]},
            "Description": {"rich_text": [{"plain_text": description}]},
            "Status": {"select": {"name": status}},
            "Priority": {"select": {"name": priority}},
            "Assignee": {"people": [{"name": assignee_name}]},
            "Due": {"date": {"start": due_date}},
            "Tags": {"multi_select": [{"name": t} for t in (tags or [])]},
        },
    }


RAW_DATABASES_FOR_TASKS = [{"id": "db-1", "title": "Sprint Board"}]


#Status normalization unit tests

def test_normalize_status_not_started():
    assert _normalize_status("Not started") == "TODO"


def test_normalize_status_in_progress():
    assert _normalize_status("In progress") == "IN_PROGRESS"


def test_normalize_status_done():
    assert _normalize_status("Done") == "DONE"


def test_normalize_status_complete():
    assert _normalize_status("Complete") == "DONE"


def test_normalize_status_case_insensitive():
    assert _normalize_status("NOT STARTED") == "TODO"
    assert _normalize_status("IN PROGRESS") == "IN_PROGRESS"
    assert _normalize_status("DONE") == "DONE"


def test_normalize_status_unknown_passthrough():
    assert _normalize_status("Blocked") == "Blocked"


#ISO-8601 date conversion unit tests

def test_to_iso8601_handles_notion_z_format():
    result = _to_iso8601("2024-01-01T00:00:00.000Z")
    assert result == "2024-01-01T00:00:00+00:00"


def test_to_iso8601_handles_date_only():
    result = _to_iso8601("2024-01-15")
    assert result == "2024-01-15"


def test_to_iso8601_handles_empty_string():
    assert _to_iso8601("") == ""


def test_to_iso8601_handles_none():
    assert _to_iso8601(None) == ""


#gather_and_store_notion_tasks: guard clauses

def test_tasks_returns_zero_when_integration_not_found():
    mock_db = make_mock_db_for_tasks(integration=None)

    result = gather_and_store_notion_tasks(integration_id=1, db=mock_db)

    assert result == 0
    mock_db.add.assert_not_called()
    mock_db.flush.assert_not_called()


def test_tasks_returns_zero_when_notion_api_key_is_none():
    integration = make_mock_integration(notion_api_key=None)
    mock_db = make_mock_db_for_tasks(integration=integration)

    result = gather_and_store_notion_tasks(integration_id=1, db=mock_db)

    assert result == 0
    mock_db.add.assert_not_called()
    mock_db.flush.assert_not_called()


def test_tasks_returns_zero_when_no_databases():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_tasks(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = []

        result = gather_and_store_notion_tasks(integration_id=1, db=mock_db)

    assert result == 0
    mock_db.add.assert_not_called()
    mock_db.flush.assert_called_once()


def test_tasks_returns_zero_when_databases_have_no_tasks():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_tasks(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES_FOR_TASKS
        MockService.return_value.fetch_tasks.return_value = []

        result = gather_and_store_notion_tasks(integration_id=1, db=mock_db)

    assert result == 0
    mock_db.add.assert_not_called()
    mock_db.flush.assert_called_once()


#gather_and_store_notion_tasks: count and inserts

def test_tasks_returns_correct_count():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_tasks(integration=integration)
    raw_tasks = [make_raw_task("task-1"), make_raw_task("task-2")]

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES_FOR_TASKS
        MockService.return_value.fetch_tasks.return_value = raw_tasks

        result = gather_and_store_notion_tasks(integration_id=1, db=mock_db)

    assert result == 2


def test_tasks_inserts_one_row_per_task():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_tasks(integration=integration)
    raw_tasks = [make_raw_task("task-1"), make_raw_task("task-2")]

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES_FOR_TASKS
        MockService.return_value.fetch_tasks.return_value = raw_tasks

        gather_and_store_notion_tasks(integration_id=1, db=mock_db)

    assert mock_db.add.call_count == 2


def test_tasks_flush_called_once():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_tasks(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES_FOR_TASKS
        MockService.return_value.fetch_tasks.return_value = [make_raw_task()]

        gather_and_store_notion_tasks(integration_id=1, db=mock_db)

    mock_db.flush.assert_called_once()


def test_tasks_fetch_tasks_called_per_database():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_tasks(integration=integration)
    two_databases = [
        {"id": "db-1", "title": "Board A"},
        {"id": "db-2", "title": "Board B"},
    ]

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = two_databases
        MockService.return_value.fetch_tasks.return_value = []

        gather_and_store_notion_tasks(integration_id=1, db=mock_db)

    assert MockService.return_value.fetch_tasks.call_count == 2
    MockService.return_value.fetch_tasks.assert_any_call(database_id="db-1")
    MockService.return_value.fetch_tasks.assert_any_call(database_id="db-2")


#gather_and_store_notion_tasks: row fields

def test_tasks_rows_have_correct_fixed_fields():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_tasks(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES_FOR_TASKS
        MockService.return_value.fetch_tasks.return_value = [make_raw_task()]

        gather_and_store_notion_tasks(integration_id=42, db=mock_db)

    added_row = mock_db.add.call_args[0][0]
    assert isinstance(added_row, WorkspaceData)
    assert added_row.type == "task"
    assert added_row.source == "notion"
    assert added_row.integration_id == 42


def test_tasks_row_title_and_status_set_correctly():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_tasks(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES_FOR_TASKS
        MockService.return_value.fetch_tasks.return_value = [
            make_raw_task(title="Deploy feature", status="Done")
        ]

        gather_and_store_notion_tasks(integration_id=1, db=mock_db)

    added_row = mock_db.add.call_args[0][0]
    assert added_row.title == "Deploy feature"
    assert added_row.status == "DONE"


def test_tasks_payload_contains_all_normalized_fields():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_tasks(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES_FOR_TASKS
        MockService.return_value.fetch_tasks.return_value = [
            make_raw_task(
                task_id="task-1",
                title="Fix bug",
                description="Something broke",
                status="In progress",
                priority="High",
                assignee_name="John Doe",
                created_time="2024-01-01T00:00:00.000Z",
                last_edited_time="2024-01-02T00:00:00.000Z",
                due_date="2024-01-15",
                tags=["backend", "urgent"],
            )
        ]

        gather_and_store_notion_tasks(integration_id=1, db=mock_db)

    payload = mock_db.add.call_args[0][0].payload
    assert payload["id"] == "task-1"
    assert payload["title"] == "Fix bug"
    assert payload["description"] == "Something broke"
    assert payload["status"] == "IN_PROGRESS"
    assert payload["priority"] == "High"
    assert payload["assignee"] == "John Doe"
    assert payload["created_at"] == "2024-01-01T00:00:00+00:00"
    assert payload["updated_at"] == "2024-01-02T00:00:00+00:00"
    assert payload["due_date"] == "2024-01-15"
    assert payload["tags"] == ["backend", "urgent"]


#gather_and_store_notion_tasks: missing/empty fields

def test_tasks_handles_missing_title():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_tasks(integration=integration)
    task = make_raw_task()
    task["properties"]["Name"]["title"] = []

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES_FOR_TASKS
        MockService.return_value.fetch_tasks.return_value = [task]

        gather_and_store_notion_tasks(integration_id=1, db=mock_db)

    assert mock_db.add.call_args[0][0].payload["title"] == ""


def test_tasks_handles_missing_status():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_tasks(integration=integration)
    task = make_raw_task()
    task["properties"]["Status"]["select"] = None

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES_FOR_TASKS
        MockService.return_value.fetch_tasks.return_value = [task]

        gather_and_store_notion_tasks(integration_id=1, db=mock_db)

    assert mock_db.add.call_args[0][0].payload["status"] == ""


def test_tasks_handles_missing_assignee():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_tasks(integration=integration)
    task = make_raw_task()
    task["properties"]["Assignee"]["people"] = []

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES_FOR_TASKS
        MockService.return_value.fetch_tasks.return_value = [task]

        gather_and_store_notion_tasks(integration_id=1, db=mock_db)

    assert mock_db.add.call_args[0][0].payload["assignee"] == ""


def test_tasks_handles_missing_due_date():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_tasks(integration=integration)
    task = make_raw_task()
    task["properties"]["Due"]["date"] = None

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES_FOR_TASKS
        MockService.return_value.fetch_tasks.return_value = [task]

        gather_and_store_notion_tasks(integration_id=1, db=mock_db)

    assert mock_db.add.call_args[0][0].payload["due_date"] == ""


def test_tasks_handles_empty_tags():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_tasks(integration=integration)
    task = make_raw_task(tags=[])

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES_FOR_TASKS
        MockService.return_value.fetch_tasks.return_value = [task]

        gather_and_store_notion_tasks(integration_id=1, db=mock_db)

    assert mock_db.add.call_args[0][0].payload["tags"] == []


def test_tasks_fetched_at_is_timezone_aware():
    integration = make_mock_integration()
    mock_db = make_mock_db_for_tasks(integration=integration)

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES_FOR_TASKS
        MockService.return_value.fetch_tasks.return_value = [make_raw_task()]

        gather_and_store_notion_tasks(integration_id=1, db=mock_db)

    assert mock_db.add.call_args[0][0].fetched_at.tzinfo is not None