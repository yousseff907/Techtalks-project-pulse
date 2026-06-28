from utils.validators import is_dangerous, is_valid_email_format

def test_is_dangerous_detects_script_injection():
	assert is_dangerous("<script>")

def test_is_dangerous_detects_command_injection():
	assert is_dangerous("; drop table users")

def test_is_dangerous_allows_clean_string():
	assert not is_dangerous("hello world")

def test_is_dangerous_detects_null_byte():
	assert is_dangerous("hello\0world")

def test_is_dangerous_detects_uppercase_protocol():
	assert is_dangerous("JavaScript:alert(1)")

def test_is_valid_email_format_returns_true_for_valid_email():
    assert is_valid_email_format("test@example.com") is True

def test_is_valid_email_format_returns_false_for_invalid_email():
    assert is_valid_email_format("invalid-email") is False