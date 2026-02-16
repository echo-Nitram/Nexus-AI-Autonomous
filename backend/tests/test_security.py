"""Tests for security utilities — password hashing and API key encryption."""

from app.services.security import hash_password, verify_password


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "my_secure_password_123"
        hashed = hash_password(password)

        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_wrong_password_fails(self):
        password = "correct_password"
        hashed = hash_password(password)

        assert verify_password("wrong_password", hashed) is False

    def test_different_hashes_for_same_password(self):
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # bcrypt generates different salts each time
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
