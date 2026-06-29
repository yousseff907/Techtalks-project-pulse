from unittest.mock import patch
from services.email_service import send_email

@patch("services.email_service.resend.Emails.send")
def	test_send_email_success(mock_email):
	mock_email.return_value = {"id": "Fake id"}
	result = send_email("noreply@gmail.com", "123456")
	assert result is True

@patch("services.email_service.resend.Emails.send")
def	test_send_email_fail(mock_email):
	mock_email.side_effect = Exception("Resend Error")
	result = send_email("fake@email.com", "012345")
	assert result is False