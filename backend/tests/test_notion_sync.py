
from unittest.mock import MagicMock, patch

from models.workspace_data import WorkspaceData
from models.workspace_integration import WorkspaceIntegrations
from services.sync.notion_sync import gather_and_store_notion_users,gather_and_store_notion_databases


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