from os import getenv
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = getenv("DATABASE_URL") # Follow this format when needing and environment variable
ENCRYPTION_KEY = getenv("ENCRYPTION_KEY")
JWT_SECRET = getenv("JWT_SECRET")
RESEND_API_KEY = getenv("RESEND_API_KEY")
APP_BASE_URL = getenv("APP_BASE_URL")