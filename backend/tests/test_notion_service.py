from unittest.mock import patch, Mock, MagicMock
from services.notion_service import NotionService

@patch("services.notion_service.requests.get")
def test_fetch_users(mock_get):
	mock_response = Mock()
	mock_response.json.return_value = {
		"results": [
			{
				"id": "123",
				"name": "John Doe",
				"person": {
					"email": "john@test.com"
				}
			},
			{
				"id": "456",
				"name": "Jane Smith",
				"person": {
					"email": ""
				}
			},
		]
	}
	mock_response.raise_for_status.return_value = None
	mock_get.return_value = mock_response

	service = NotionService("token")
	result = service.fetch_users()

	assert result[0] == {
		"id": "123",
		"name": "John Doe",
		"email": "john@test.com",
        "active": False,
	}

	assert result[1] == {
		"id": "456",
		"name": "Jane Smith",
		"email": "",
         "active": False,
	}


def test_fetch_databases_returns_list_of_dicts():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {
                "id": "db-1",
                "title": [{"plain_text": "Project Tracker"}],
            }
        ],
        "has_more": False,
    }

    with patch("requests.post", return_value=mock_response):
        service = NotionService(api_token="test-token")
        result = service.fetch_databases()

    assert result == [{"id": "db-1", "title": "Project Tracker"}]


def test_fetch_databases_returns_multiple_databases():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {"id": "db-1", "title": [{"plain_text": "Project Tracker"}]},
            {"id": "db-2", "title": [{"plain_text": "Bug Reports"}]},
        ],
        "has_more": False,
    }

    with patch("requests.post", return_value=mock_response):
        service = NotionService(api_token="test-token")
        result = service.fetch_databases()

    assert len(result) == 2
    assert result[1] == {"id": "db-2", "title": "Bug Reports"}


def test_fetch_databases_handles_missing_title_array():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [{"id": "db-1"}],  # no title key at all
        "has_more": False,
    }

    with patch("requests.post", return_value=mock_response):
        service = NotionService(api_token="test-token")
        result = service.fetch_databases()

    assert result == [{"id": "db-1", "title": ""}]


def test_fetch_databases_handles_empty_title_array():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [{"id": "db-1", "title": []}],  # title key exists but empty
        "has_more": False,
    }

    with patch("requests.post", return_value=mock_response):
        service = NotionService(api_token="test-token")
        result = service.fetch_databases()

    assert result == [{"id": "db-1", "title": ""}]


def test_fetch_databases_handles_missing_id():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [{"title": [{"plain_text": "Orphan DB"}]}],  # no id key
        "has_more": False,
    }

    with patch("requests.post", return_value=mock_response):
        service = NotionService(api_token="test-token")
        result = service.fetch_databases()

    assert result == [{"id": "", "title": "Orphan DB"}]


def test_fetch_databases_returns_empty_list_when_no_results():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [],
        "has_more": False,
    }

    with patch("requests.post", return_value=mock_response):
        service = NotionService(api_token="test-token")
        result = service.fetch_databases()

    assert result == []
    
def test_fetch_databases_follows_pagination():
    first_page = MagicMock()
    first_page.json.return_value = {
        "results": [
            {"id": "db-1", "title": [{"plain_text": "First DB"}]},
        ],
        "has_more": True,
        "next_cursor": "cursor-abc",
    }

    second_page = MagicMock()
    second_page.json.return_value = {
        "results": [
            {"id": "db-2", "title": [{"plain_text": "Second DB"}]},
        ],
        "has_more": False,
    }

    with patch("requests.post", side_effect=[first_page, second_page]):
        service = NotionService(api_token="test-token")
        result = service.fetch_databases()

    assert len(result) == 2
    assert result[0] == {"id": "db-1", "title": "First DB"}
    assert result[1] == {"id": "db-2", "title": "Second DB"}


def test_fetch_databases_passes_cursor_on_second_request():
    first_page = MagicMock()
    first_page.json.return_value = {
        "results": [{"id": "db-1", "title": [{"plain_text": "DB One"}]}],
        "has_more": True,
        "next_cursor": "cursor-xyz",
    }

    second_page = MagicMock()
    second_page.json.return_value = {
        "results": [],
        "has_more": False,
    }

    with patch("requests.post", side_effect=[first_page, second_page]) as mock_post:
        service = NotionService(api_token="test-token")
        service.fetch_databases()

    # Confirm the second call included the cursor in the request body
    second_call_body = mock_post.call_args_list[1].kwargs["json"]
    assert second_call_body.get("start_cursor") == "cursor-xyz"