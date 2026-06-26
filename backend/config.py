from os import getenv
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = getenv("DATABASE_URL") # Follow this format when needing and environment variable
ENCRYPTION_KEY = getenv("ENCRYPTION_KEY")