from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIGURE = ROOT / "scripts" / "configure_local_database_credentials.py"
ALEMBIC = ROOT / "scripts" / "alembic_local.sh"


def test_local_credential_config_separates_runtime_from_migrator() -> None:
    text = CONFIGURE.read_text(encoding="utf-8")
    assert 'TARGET_DBA = "dacqua_dolce_dba"' in text
    assert 'TARGET_APP = "dacqua_dolce_app"' in text
    assert "DACQUA_DB_MIGRATOR_PASSWORD" in text
    assert "DACQUA_DB_APP_PASSWORD" in text
    assert 'remove={"DACQUA_MIGRATION_DATABASE_URL"}' in text


def test_local_alembic_wrapper_uses_migrator_only_for_migrations() -> None:
    text = ALEMBIC.read_text(encoding="utf-8")
    assert "DACQUA_DB_MIGRATOR_PASSWORD" in text
    assert "dacqua_dolce_migrator" in text
    assert "DACQUA_MIGRATION_DATABASE_URL" in text
    assert ".venv/bin/alembic" in text
    assert "dacqua_dolce_dev" in text
