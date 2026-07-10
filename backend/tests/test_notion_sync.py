from unittest.mock import patch

from models.workspace import Workspace
from models.workspace_data import WorkspaceData
from models.workspace_integration import WorkspaceIntegrations
from services.sync.notion_sync import gather_and_store_notion_users, gather_and_store_notion_databases

from utils.encryption import encrypt


RAW_DATABASES = [
    {"id": "db-1", "title": "Project Tracker"},
    {"id": "db-2", "title": "Bug Reports"},
]

RAW_USERS = [
    {"id": "user-1", "name": "John Doe", "email": "john@example.com"},
    {"id": "user-2", "name": "Jane Smith", "email": "jane@example.com"},
]


def make_workspace_with_integration(db_session, notion_api_key="test-notion-token", invite_code="notiontest"):
    workspace = Workspace(
        name="Notion Sync WS",
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


# gather_and_store_notion_users tests

def test_returns_zero_when_integration_not_found(db_session):
    result = gather_and_store_notion_users(integration_id=999999, db=db_session)

    assert result == 0
    assert db_session.query(WorkspaceData).count() == 0


def test_returns_zero_when_notion_api_key_is_none(db_session):
    workspace, integration = make_workspace_with_integration(db_session, notion_api_key=None, invite_code="notionnokey")

    result = gather_and_store_notion_users(integration_id=workspace.id, db=db_session)

    assert result == 0
    assert db_session.query(WorkspaceData).filter(WorkspaceData.integration_id == workspace.id).count() == 0


def test_returns_zero_when_no_users_returned(db_session):
    workspace, integration = make_workspace_with_integration(db_session, invite_code="notionnousers")

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_users.return_value = []

        result = gather_and_store_notion_users(integration_id=workspace.id, db=db_session)

    assert result == 0
    assert db_session.query(WorkspaceData).filter(WorkspaceData.integration_id == workspace.id).count() == 0


def test_returns_correct_count_of_users_stored(db_session):
    workspace, integration = make_workspace_with_integration(db_session, invite_code="notionusercount")

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_users.return_value = RAW_USERS

        result = gather_and_store_notion_users(integration_id=workspace.id, db=db_session)

    assert result == 2


def test_inserts_one_row_per_user(db_session):
    workspace, integration = make_workspace_with_integration(db_session, invite_code="notionuserrows")

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_users.return_value = RAW_USERS

        gather_and_store_notion_users(integration_id=workspace.id, db=db_session)

    db_session.commit()

    rows = db_session.query(WorkspaceData).filter(
        WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "user"
    ).all()
    assert len(rows) == 2


def test_workspace_data_rows_have_correct_fixed_fields(db_session):
    workspace, integration = make_workspace_with_integration(db_session, invite_code="notionfixedfields")

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_users.return_value = RAW_USERS

        gather_and_store_notion_users(integration_id=workspace.id, db=db_session)

    db_session.commit()

    rows = db_session.query(WorkspaceData).filter(
        WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "user"
    ).all()

    for row in rows:
        assert row.type == "user"
        assert row.source == "notion"
        assert row.integration_id == workspace.id


def test_workspace_data_payload_contains_normalized_fields(db_session):
    workspace, integration = make_workspace_with_integration(db_session, invite_code="notionpayload")

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_users.return_value = RAW_USERS

        gather_and_store_notion_users(integration_id=workspace.id, db=db_session)

    db_session.commit()

    rows = db_session.query(WorkspaceData).filter(
        WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "user"
    ).order_by(WorkspaceData.id).all()

    assert rows[0].payload == {
        "id": "user-1",
        "name": "John Doe",
        "email": "john@example.com",
    }
    assert rows[1].payload == {
        "id": "user-2",
        "name": "Jane Smith",
        "email": "jane@example.com",
    }


def test_workspace_data_payload_excludes_extra_fields(db_session):
    workspace, integration = make_workspace_with_integration(db_session, invite_code="notionpayloadextra")

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

        gather_and_store_notion_users(integration_id=workspace.id, db=db_session)

    db_session.commit()

    row = db_session.query(WorkspaceData).filter(
        WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "user"
    ).first()

    assert set(row.payload.keys()) == {"id", "name", "email"}


def test_workspace_data_fetched_at_is_timezone_aware(db_session):
    workspace, integration = make_workspace_with_integration(db_session, invite_code="notionfetchedat1")

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_users.return_value = RAW_USERS[:1]

        gather_and_store_notion_users(integration_id=workspace.id, db=db_session)

    db_session.commit()

    row = db_session.query(WorkspaceData).filter(
        WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "user"
    ).first()

    assert row is not None
    assert row.fetched_at.tzinfo is not None


def test_notion_service_instantiated_with_correct_token(db_session):
    workspace, integration = make_workspace_with_integration(db_session, notion_api_key="secret-token-abc", invite_code="notiontoken")

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_users.return_value = []
        gather_and_store_notion_users(integration_id=workspace.id, db=db_session)

    MockService.assert_called_once_with(api_token="secret-token-abc")


# gather_and_store_notion_databases tests

def test_databases_returns_zero_when_integration_not_found(db_session):
    result = gather_and_store_notion_databases(integration_id=999999, db=db_session)

    assert result == 0
    assert db_session.query(WorkspaceData).count() == 0


def test_databases_returns_zero_when_notion_api_key_is_none(db_session):
    workspace, integration = make_workspace_with_integration(db_session, notion_api_key=None, invite_code="notiondbnokey")

    result = gather_and_store_notion_databases(integration_id=workspace.id, db=db_session)

    assert result == 0
    assert db_session.query(WorkspaceData).filter(WorkspaceData.integration_id == workspace.id).count() == 0


def test_databases_returns_zero_when_no_databases_returned(db_session):
    workspace, integration = make_workspace_with_integration(db_session, invite_code="notiondbnoresults")

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = []

        result = gather_and_store_notion_databases(integration_id=workspace.id, db=db_session)

    assert result == 0
    assert db_session.query(WorkspaceData).filter(WorkspaceData.integration_id == workspace.id).count() == 0


def test_databases_returns_correct_count(db_session):
    workspace, integration = make_workspace_with_integration(db_session, invite_code="notiondbcount")

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES

        result = gather_and_store_notion_databases(integration_id=workspace.id, db=db_session)

    assert result == 2


def test_databases_inserts_one_row_per_database(db_session):
    workspace, integration = make_workspace_with_integration(db_session, invite_code="notiondbrows")

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES

        gather_and_store_notion_databases(integration_id=workspace.id, db=db_session)

    db_session.commit()

    rows = db_session.query(WorkspaceData).filter(
        WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "project"
    ).all()
    assert len(rows) == 2


def test_databases_rows_have_correct_fixed_fields(db_session):
    workspace, integration = make_workspace_with_integration(db_session, invite_code="notiondbfixedfields")

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES

        gather_and_store_notion_databases(integration_id=workspace.id, db=db_session)

    db_session.commit()

    rows = db_session.query(WorkspaceData).filter(
        WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "project"
    ).all()

    for row in rows:
        assert row.type == "project"
        assert row.source == "notion"
        assert row.integration_id == workspace.id


def test_databases_title_is_set_on_row(db_session):
    workspace, integration = make_workspace_with_integration(db_session, invite_code="notiondbtitle")

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES

        gather_and_store_notion_databases(integration_id=workspace.id, db=db_session)

    db_session.commit()

    rows = db_session.query(WorkspaceData).filter(
        WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "project"
    ).order_by(WorkspaceData.id).all()

    assert rows[0].title == "Project Tracker"
    assert rows[1].title == "Bug Reports"


def test_databases_payload_contains_normalized_fields(db_session):
    workspace, integration = make_workspace_with_integration(db_session, invite_code="notiondbpayload")

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES

        gather_and_store_notion_databases(integration_id=workspace.id, db=db_session)

    db_session.commit()

    rows = db_session.query(WorkspaceData).filter(
        WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "project"
    ).order_by(WorkspaceData.id).all()

    assert rows[0].payload == {"id": "db-1", "title": "Project Tracker"}
    assert rows[1].payload == {"id": "db-2", "title": "Bug Reports"}


def test_databases_payload_excludes_extra_fields(db_session):
    workspace, integration = make_workspace_with_integration(db_session, invite_code="notiondbpayloadextra")

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

        gather_and_store_notion_databases(integration_id=workspace.id, db=db_session)

    db_session.commit()

    row = db_session.query(WorkspaceData).filter(
        WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "project"
    ).first()

    assert set(row.payload.keys()) == {"id", "title"}


def test_databases_fetched_at_is_timezone_aware(db_session):
    workspace, integration = make_workspace_with_integration(db_session, invite_code="notiondbfetchedat")

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = RAW_DATABASES[:1]

        gather_and_store_notion_databases(integration_id=workspace.id, db=db_session)

    db_session.commit()

    row = db_session.query(WorkspaceData).filter(
        WorkspaceData.integration_id == workspace.id, WorkspaceData.type == "project"
    ).first()

    assert row is not None
    assert row.fetched_at.tzinfo is not None


def test_databases_notion_service_instantiated_with_correct_token(db_session):
    workspace, integration = make_workspace_with_integration(db_session, notion_api_key="secret-db-token", invite_code="notiondbtoken")

    with patch("services.sync.notion_sync.NotionService") as MockService:
        MockService.return_value.fetch_databases.return_value = []
        gather_and_store_notion_databases(integration_id=workspace.id, db=db_session)

    MockService.assert_called_once_with(api_token="secret-db-token")