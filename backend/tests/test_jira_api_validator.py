from unittest.mock import patch, Mock
from utils.jira_api_validator import is_valid_jira_credentials

@patch("utils.jira_api_validator.get")
def	test_jira_api_validation(mock_get: Mock):
	mock_response = Mock()
	mock_response.status_code = 401
	mock_get.return_value = mock_response

	assert not is_valid_jira_credentials("https://example.atlassian.net", "email@test.com", "wrongtoken")
	
	mock_response.status_code = 200
	mock_get.return_value = mock_response

	assert is_valid_jira_credentials("https://example.atlassian.net", "email@test.com", "validtoken")