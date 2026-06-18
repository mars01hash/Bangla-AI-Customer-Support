import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

import pytest
from jose import jwt
from app.config import settings
from app.auth import get_password_hash, verify_password, create_access_token

def test_password_hashing():
    password = "SuperSecretPassword123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_jwt_token_generation():
    payload = {"sub": "test@example.com", "role": "customer"}
    token = create_access_token(payload)
    
    decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == "test@example.com"
    assert decoded["role"] == "customer"
    assert "exp" in decoded
