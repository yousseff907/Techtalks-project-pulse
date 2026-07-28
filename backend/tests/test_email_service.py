from unittest.mock import patch

from services.email_service import _format_summary, send_email, send_summary_email


def _sent_params(mock_email):
	# _send_email calls resend.Emails.send(params) with one positional dict.
	return mock_email.call_args.args[0]


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


@patch("services.email_service.resend.Emails.send")
def	test_sender_is_project_pulse(mock_email):
	mock_email.return_value = {"id": "x"}
	send_email("user@example.com", "246810")
	params = _sent_params(mock_email)
	assert params["from"].startswith("Project Pulse")
	assert "easyrecipe.online" in params["from"]


@patch("services.email_service.resend.Emails.send")
def	test_verification_email_contains_code_and_expiry(mock_email):
	mock_email.return_value = {"id": "x"}
	send_email("user@example.com", "246810")
	html = _sent_params(mock_email)["html"]
	assert "246810" in html
	assert "15 minutes" in html


@patch("services.email_service.resend.Emails.send")
def	test_summary_email_contains_name_cta_and_blocks(mock_email):
	mock_email.return_value = {"id": "x"}
	summary = "First paragraph.\n\n- risk one\n- risk two"
	result = send_summary_email("user@example.com", summary, "Acme Team", 42)
	assert result is True
	params = _sent_params(mock_email)
	html = params["html"]
	assert "Acme Team" in html
	assert "/workspaces/42/dashboard" in html
	assert "<p" in html and "<li" in html
	assert params["from"].startswith("Project Pulse")


def	test_format_summary_splits_paragraphs():
	out = _format_summary("Para one.\n\nPara two.")
	assert out.count("<p") == 2
	assert "Para one." in out
	assert "Para two." in out


def	test_format_summary_renders_bullets_and_bold():
	out = _format_summary("- **High** priority\n- second item")
	assert "<ul" in out
	assert out.count("<li") == 2
	assert "<strong>High</strong>" in out


def	test_format_summary_groups_inline_bullets():
	# Lead-in line directly followed by bullets, no blank line between.
	out = _format_summary("Key risks:\n- one\n- two")
	assert "<ul" in out
	assert out.count("<li") == 2
	assert "Key risks:" in out
	assert "- one" not in out  # dash consumed into the <li>, not left as text


def	test_format_summary_renders_ordered_list():
	out = _format_summary("1. first\n2. second")
	assert "<ol" in out
	assert out.count("<li") == 2


def	test_format_summary_escapes_html():
	out = _format_summary("5 < 10 & climbing <script>alert(1)</script>")
	assert "&lt;" in out
	assert "&amp;" in out
	assert "<script>" not in out


def	test_format_summary_handles_empty():
	out = _format_summary("   ")
	assert "<p" in out
