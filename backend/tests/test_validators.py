from utils.validators import is_dangerous

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