from __future__ import annotations

import pytest

from app.core.config import Settings


@pytest.mark.unit
def test_allowed_origins_parses_csv() -> None:
    settings = Settings(ALLOWED_ORIGINS="http://a.local, http://b.local")
    assert settings.allowed_origins_list == ["http://a.local", "http://b.local"]


@pytest.mark.unit
def test_allowed_origins_parses_json() -> None:
    settings = Settings(ALLOWED_ORIGINS='["http://a.local", "http://b.local"]')
    assert settings.allowed_origins_list == ["http://a.local", "http://b.local"]


@pytest.mark.unit
def test_production_validation_requires_entra_and_secure_local_auth_disabled() -> None:
    settings = Settings(ENVIRONMENT="production")
    with pytest.raises(RuntimeError):
        settings.validate_production()


@pytest.mark.unit
def test_production_validation_passes_with_required_values() -> None:
    settings = Settings(
        ENVIRONMENT="production",
        ENTRA_TENANT_ID="tenant",
        ENTRA_CLIENT_ID="client",
        ENTRA_AUDIENCE="audience",
        KEY_VAULT_URI="https://vault.local",
        CSRF_SECRET="non-default-secret",
        LOCAL_AUTH_ENABLED=False,
    )
    settings.validate_production()
