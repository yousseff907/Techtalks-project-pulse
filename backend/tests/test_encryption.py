from utils.encryption import encrypt, decrypt

def	test_encryption_decryption():
	value = "Hello World"
	encrypted = encrypt(value)
	assert encrypted != value
	decrypted = decrypt(encrypted)
	assert decrypted == value