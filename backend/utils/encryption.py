from config import ENCRYPTION_KEY
from cryptography.fernet import Fernet

fernet = Fernet(ENCRYPTION_KEY)

def encrypt(value: str) -> str:
	return fernet.encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
	return fernet.decrypt(value.encode()).decode()