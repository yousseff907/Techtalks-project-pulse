import os
from cryptography.fernet import Fernet
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.database import Base, get_db
from app import app


os.environ.setdefault("ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("JWT_SECRET", Fernet.generate_key().decode())
os.environ.setdefault("DATABASE_URL", "postgresql://testuser:testpass@localhost:5432/testdb")

engine = create_engine(os.environ["DATABASE_URL"])
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture(scope="function")
def	db_session():
	Base.metadata.create_all(bind=engine)
	session = TestingSessionLocal()

	def	override_get_db():
		yield session

	app.dependency_overrides[get_db] = override_get_db
	yield session
	session.close()

	Base.metadata.drop_all(bind=engine)
	app.dependency_overrides.clear()