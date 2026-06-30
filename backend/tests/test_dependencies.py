# import os
# os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from unittest.mock import patch, Mock
import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from utils.dependencies import get_current_user


@pytest.fixture
def mock_db():
    return Mock()


@pytest.fixture
def mock_credentials():
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials="mocked_jwt_string")


@patch("utils.dependencies.verify_jwt_token")
def test_get_current_user_invalid_token(mock_verify, mock_credentials, mock_db):
    mock_verify.return_value = None
    
    with pytest.raises(HTTPException) as exc:
        get_current_user(credentials=mock_credentials, db=mock_db)
        
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Invalid or expired token"


@patch("utils.dependencies.verify_jwt_token")
def test_get_current_user_not_found_in_db(mock_verify, mock_credentials, mock_db):
    mock_verify.return_value = {"uid": 999, "email": "ghost@test.com"}
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc:
        get_current_user(credentials=mock_credentials, db=mock_db)
        
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "User not found"


@patch("utils.dependencies.verify_jwt_token")
def test_get_current_user_not_verified(mock_verify, mock_credentials, mock_db):
    mock_verify.return_value = {"uid": 1, "email": "unverified@test.com"}
    
    mock_user = Mock()
    mock_user.id = 1
    mock_user.is_verified = False
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    
    with pytest.raises(HTTPException) as exc:
        get_current_user(credentials=mock_credentials, db=mock_db)
        
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc.value.detail == "Please verify your email first"


@patch("utils.dependencies.verify_jwt_token")
def test_get_current_user_success(mock_verify, mock_credentials, mock_db):
    mock_verify.return_value = {"uid": 1, "email": "verified@test.com"}
    
    mock_user = Mock()
    mock_user.id = 1
    mock_user.is_verified = True
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    
    result = get_current_user(credentials=mock_credentials, db=mock_db)
    
    assert result == mock_user
    mock_db.query.assert_called_once()
