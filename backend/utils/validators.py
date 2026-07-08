import re


DANGEROUS_CHARS = [
    # Script injection
    '<',
    '>',
    '"',
    "'",
    
    # Command injection
    ';',
    '|',
    '`',
    '$(',
    '${',
    
    # Path traversal
    '..',
    '\\',
    
    # Null bytes
    '\0',
    '%00',
    
    # Protocol exploits
    'javascript:',
    'data:',
    'file:',
    'vbscript:',
    'about:',
    
    # Additional command chars
    '\n',  # newline
    '\r',  # carriage return
    '&&',  # command chain
    '||',  # command OR
    
    # Format string attacks
    '%n',
    '%s',
    '%x',
]

def is_dangerous(string: str) -> bool:
	string = string.lower()
	for char in DANGEROUS_CHARS:
		if char in string:
			return True
	return False

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)

def is_valid_email_format(email: str) -> bool:
	
    if not email or len(email) > 254:
        return False
    return bool(EMAIL_REGEX.match(email))

def is_blank(string: str) -> bool:
    if not string:
        return True

    if string.strip() == "":
        return True

    return False