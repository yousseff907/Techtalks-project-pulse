from utils.validators import is_dangerous

def test_is_dangerous_detects_script_injection():
	assert is_dangerous("<script>") == True

def test_is_dangerous_detects_command_injection():
	assert is_dangerous("; drop table users") == True

def test_is_dangerous_allows_clean_string():
	assert is_dangerous("hello world") == False

def test_is_dangerous_detects_null_byte():
	assert is_dangerous("hello\0world") == True