"""Tests for JWT authentication."""

from app.api.auth import create_access_token, ALGORITHM
from jose import jwt
from app.config import get_settings


class TestJWTTokens:
    def test_create_access_token(self):
        token = create_access_token(data={"sub": "test-user-id"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_subject(self):
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = create_access_token(data={"sub": user_id})

        settings = get_settings()
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        assert payload["sub"] == user_id
        assert "exp" in payload

    def test_token_contains_expiration(self):
        token = create_access_token(data={"sub": "test"})
        settings = get_settings()
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        assert "exp" in payload
