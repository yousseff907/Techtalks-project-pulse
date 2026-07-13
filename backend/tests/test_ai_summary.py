from unittest.mock import Mock, patch

from models.user import User
from models.workspace import Workspace
from models.workspace_data import WorkspaceData
from models.workspace_integration import WorkspaceIntegrations
from services.ai_summary import generate_workspace_summary


@patch("services.ai_summary.genai.Client")
def test_generate_workspace_summary_success(mock_client, db_session):
    owner = User(
        username="owner",
        email="owner@example.com",
        is_verified=True,
    )
    db_session.add(owner)
    db_session.flush()

    workspace = Workspace(
        name="Workspace",
        created_by=owner.id,
        invite_code="code",
        invite_link="link",
    )
    db_session.add(workspace)
    db_session.flush()

    db_session.add(
    WorkspaceIntegrations(
        workspace_id=workspace.id,
    )
)
    db_session.flush()

    db_session.add_all([
        WorkspaceData(
            integration_id=workspace.id,
            type="task",
            source="jira",
            payload={
                "title": "Fix login",
                "status": "TODO",
                "priority": "High",
                "due_date": "2024-01-01",
            },
        ),
        WorkspaceData(
            integration_id=workspace.id,
            type="task",
            source="jira",
            payload={
                "title": "Dashboard",
                "status": "DONE",
                "priority": "Low",
            },
        ),
    ])

    db_session.commit()
    
    response = Mock()
    response.text = "Generated summary"

    client = Mock()
    client.models.generate_content.return_value = response

    mock_client.return_value = client

    summary = generate_workspace_summary(
        workspace.id,
        db_session,
    )

    assert summary == "Generated summary"

    prompt = client.models.generate_content.call_args.kwargs["contents"]

    assert "Total tasks: 2" in prompt
    assert "TODO: 1" in prompt
    assert "DONE: 1" in prompt
    assert "Fix login" in prompt

@patch("services.ai_summary.genai.Client")
def test_generate_workspace_summary_api_failure(
    mock_client,
    db_session,
):
    owner = User(
        username="owner",
        email="owner@example.com",
        is_verified=True,
    )
    db_session.add(owner)
    db_session.flush()

    workspace = Workspace(
        name="Workspace",
        created_by=owner.id,
        invite_code="code",
        invite_link="link",
    )
    db_session.add(workspace)
    db_session.flush()

    db_session.add(
        WorkspaceIntegrations(
            workspace_id=workspace.id,
        )
    )

    db_session.commit()

    client = Mock()
    client.models.generate_content.side_effect = Exception(
        "Gemini unavailable"
    )

    mock_client.return_value = client

    import pytest

    with pytest.raises(RuntimeError):
        generate_workspace_summary(
            workspace.id,
            db_session,
        )