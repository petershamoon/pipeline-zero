"""Unit tests for the auth service functions."""
from __future__ import annotations

import hashlib

import pytest

from app.services.auth import (
    _hash_token,
    hash_password,
    verify_csrf_token,
    verify_password,
)


@pytest.mark.unit
class TestPasswordHashing:
    """Tests for hash_password / verify_password round-trip."""

    def test_hash_and_verify_correct_password(self) -> None:
        """Hashing a password and verifying the same password returns True."""
        plain = "correct-horse-battery-staple"
        hashed = hash_password(plain)

        assert hashed != plain, "hash must not be the plaintext password"
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password_returns_false(self) -> None:
        """Verifying with the wrong password returns False."""
        hashed = hash_password("my-secret-password")
        assert verify_password("wrong-password", hashed) is False

    def test_hash_produces_different_hashes_for_same_input(self) -> None:
        """Argon2 uses random salts, so two hashes of the same input differ."""
        plain = "same-password"
        hash1 = hash_password(plain)
        hash2 = hash_password(plain)

        assert hash1 != hash2, "each hash call should produce a unique value"
        # Both should still verify correctly
        assert verify_password(plain, hash1) is True
        assert verify_password(plain, hash2) is True

    def test_verify_with_empty_password_returns_false(self) -> None:
        """Verifying an empty string against a real hash returns False."""
        hashed = hash_password("real-password")
        assert verify_password("", hashed) is False

    def test_hash_output_starts_with_argon2_prefix(self) -> None:
        """Argon2 hashes should start with the $argon2 prefix."""
        hashed = hash_password("test-password")
        assert hashed.startswith("$argon2"), f"Expected argon2 prefix, got: {hashed[:20]}"


@pytest.mark.unit
class TestHashToken:
    """Tests for the internal _hash_token utility."""

    def test_produces_sha256_hex_digest(self) -> None:
        """_hash_token should return a SHA-256 hex digest."""
        value = "test-token-value"
        result = _hash_token(value)
        expected = hashlib.sha256(value.encode("utf-8")).hexdigest()

        assert result == expected
        assert len(result) == 64  # SHA-256 produces 64-char hex string

    def test_deterministic_output(self) -> None:
        """Same input always produces the same hash."""
        value = "deterministic-check"
        assert _hash_token(value) == _hash_token(value)

    def test_different_inputs_produce_different_hashes(self) -> None:
        """Different inputs must produce different hashes."""
        assert _hash_token("alpha") != _hash_token("beta")


@pytest.mark.unit
class TestVerifyCsrfToken:
    """Tests for verify_csrf_token."""

    @staticmethod
    def _make_session_with_csrf(raw_csrf: str):
        """Create a minimal mock session object with the csrf_token_hash set."""

        class FakeSession:
            csrf_token_hash: str

        session = FakeSession()
        session.csrf_token_hash = _hash_token(raw_csrf)
        return session

    def test_valid_csrf_token_passes(self) -> None:
        """When cookie and header match, and hash matches session, returns True."""
        raw_csrf = "valid-csrf-token-value"
        session = self._make_session_with_csrf(raw_csrf)

        assert verify_csrf_token(
            raw_csrf_cookie=raw_csrf,
            raw_csrf_header=raw_csrf,
            session_obj=session,
        ) is True

    def test_missing_csrf_cookie_fails(self) -> None:
        """When csrf cookie is None, returns False."""
        raw_csrf = "some-csrf-value"
        session = self._make_session_with_csrf(raw_csrf)

        assert verify_csrf_token(
            raw_csrf_cookie=None,
            raw_csrf_header=raw_csrf,
            session_obj=session,
        ) is False

    def test_missing_csrf_header_fails(self) -> None:
        """When csrf header is None, returns False."""
        raw_csrf = "some-csrf-value"
        session = self._make_session_with_csrf(raw_csrf)

        assert verify_csrf_token(
            raw_csrf_cookie=raw_csrf,
            raw_csrf_header=None,
            session_obj=session,
        ) is False

    def test_cookie_and_header_mismatch_fails(self) -> None:
        """When cookie and header values differ, returns False."""
        raw_csrf = "correct-csrf"
        session = self._make_session_with_csrf(raw_csrf)

        assert verify_csrf_token(
            raw_csrf_cookie=raw_csrf,
            raw_csrf_header="different-value",
            session_obj=session,
        ) is False

    def test_cookie_matches_header_but_not_session_hash_fails(self) -> None:
        """When cookie == header but they don't match the session hash, returns False."""
        session = self._make_session_with_csrf("original-csrf")
        wrong_csrf = "wrong-csrf-value"

        assert verify_csrf_token(
            raw_csrf_cookie=wrong_csrf,
            raw_csrf_header=wrong_csrf,
            session_obj=session,
        ) is False

    def test_empty_string_csrf_cookie_fails(self) -> None:
        """Empty strings should fail the truthy check."""
        session = self._make_session_with_csrf("something")

        assert verify_csrf_token(
            raw_csrf_cookie="",
            raw_csrf_header="",
            session_obj=session,
        ) is False

    def test_both_none_fails(self) -> None:
        """Both cookie and header as None should fail."""
        session = self._make_session_with_csrf("something")

        assert verify_csrf_token(
            raw_csrf_cookie=None,
            raw_csrf_header=None,
            session_obj=session,
        ) is False
