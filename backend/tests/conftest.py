import os
from cryptography.fernet import Fernet

os.environ.setdefault("ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("JWT_SECRET", Fernet.generate_key().decode())
os.environ.setdefault("DATABASE_URL", "postgresql://testuser:testpass@localhost:5432/testdb")
os.environ.setdefault("APP_BASE_URL", "https://example.com")

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.database import Base, get_db
from utils.dependencies import get_current_user
from app import app



@pytest.fixture(scope="function")
def	db_session():

	engine = create_engine(os.environ["DATABASE_URL"])
	TestingSessionLocal = sessionmaker(bind=engine)

	Base.metadata.create_all(bind=engine)
	session = TestingSessionLocal()

	def	override_get_db():
		yield session

	app.dependency_overrides[get_db] = override_get_db
	yield session
	session.close()

	Base.metadata.drop_all(bind=engine)
	app.dependency_overrides.pop(get_db, None)

@pytest.fixture(scope="function")
def	mock_user():
	mock_user = Mock()

	def	override_get_current_user():
		return mock_user
	
	app.dependency_overrides[get_current_user] = override_get_current_user
	yield mock_user
	app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture(scope="function")
def mock_redis_client():
	mock_redis = MagicMock()
	with patch("routes.workspaces.redis_client", mock_redis):
		yield mock_redis

