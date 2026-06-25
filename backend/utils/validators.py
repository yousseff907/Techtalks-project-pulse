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
	for char in DANGEROUS_CHARS:
		if char in string:
			return True
	return False