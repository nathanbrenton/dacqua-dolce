from app.core.config import Settings


RUNTIME_URL = (
    "postgresql+psycopg://runtime:unused@127.0.0.1/runtime"
)

MIGRATION_URL = (
    "postgresql+psycopg://migrator:unused@127.0.0.1/runtime"
)


def test_alembic_database_url_falls_back_to_runtime_url() -> None:
    settings = Settings(
        database_url=RUNTIME_URL,
        migration_database_url=None,
    )

    assert settings.alembic_database_url == RUNTIME_URL


def test_alembic_database_url_prefers_migration_url() -> None:
    settings = Settings(
        database_url=RUNTIME_URL,
        migration_database_url=MIGRATION_URL,
    )

    assert settings.database_url == RUNTIME_URL
    assert settings.alembic_database_url == MIGRATION_URL
