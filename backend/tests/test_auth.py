import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.security.password import hash_password, verify_password
from app.security.jwt import create_access_token, decode_access_token

def test_password_hashing():
    pw = "secretpassword123"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_jwt_generation_and_decoding():
    subject = "user@test.com"
    token = create_access_token(subject=subject)
    assert token is not None
    decoded = decode_access_token(token)
    assert decoded == subject
