import pytest
from pydantic import ValidationError

from app.core.config import Settings


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "database_url": "sqlite+pysqlite:///:memory:",
        **overrides,
    }
    return Settings(**values)


def test_environment_identities_are_first_class() -> None:
    development = make_settings(environment="development")
    testing = make_settings(environment="test")
    production = make_settings(environment="production")

    assert development.is_development
    assert not development.is_test
    assert not development.is_production

    assert testing.is_test
    assert not testing.is_development
    assert not testing.is_production

    assert production.is_production
    assert not production.is_development
    assert not production.is_test


def test_legacy_environment_aliases_are_canonicalized() -> None:
    assert make_settings(environment="dev").environment == "development"
    assert make_settings(environment="testing").environment == "test"
    assert make_settings(environment="prod").environment == "production"


def test_unknown_environment_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make_settings(environment="staging-ish")
