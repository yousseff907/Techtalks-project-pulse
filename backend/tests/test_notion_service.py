from unittest.mock import patch, Mock
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
		"email": "john@test.com"
	}

	assert result[1] == {
		"id": "456",
		"name": "Jane Smith",
		"email": ""
	}