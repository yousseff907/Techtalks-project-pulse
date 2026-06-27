from unittest.mock import patch, Mock
from utils.notion_api_validator import is_valid_notion_credentials


@patch("utils.notion_api_validator.get")
def test_notion_api_validation(mock_get: Mock):
    mock_response = Mock()
    mock_response.status_code = 401
    mock_get.return_value = mock_response

    assert not is_valid_notion_credentials("wrongtoken")
    
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    assert is_valid_notion_credentials("validtoken")