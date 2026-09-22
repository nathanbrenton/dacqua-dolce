from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

INIT_SCRIPT = (
    ROOT
    / "infra"
    / "production"
    / "postgresql"
    / "init_database.sh"
)

API_UNIT = (
    ROOT
    / "infra"
    / "production"
    / "systemd"
    / "dacqua-dolce-api.service"
)


def test_production_database_bootstrap_splits_roles() -> None:
    text = INIT_SCRIPT.read_text(encoding="utf-8")

    assert "dacqua_dolce_migrator" in text
    assert "dacqua_dolce_app" in text

    assert (
        "--owner=dacqua_dolce_migrator"
        in text
    )

    assert (
        "ALTER DATABASE dacqua_dolce "
        "OWNER TO dacqua_dolce_migrator"
        in text
    )

    assert (
        "REASSIGN OWNED BY dacqua_dolce_app "
        "TO dacqua_dolce_migrator"
        in text
    )


def test_runtime_role_cannot_create_schema_objects() -> None:
    text = INIT_SCRIPT.read_text(encoding="utf-8")

    assert (
        "REVOKE CREATE ON SCHEMA public "
        "FROM dacqua_dolce_app"
        in text
    )

    assert (
        "GRANT USAGE ON SCHEMA public "
        "TO dacqua_dolce_app"
        in text
    )


def test_runtime_role_receives_dml_not_ddl() -> None:
    text = INIT_SCRIPT.read_text(encoding="utf-8")

    assert "GRANT SELECT, INSERT, UPDATE, DELETE" in text
    assert "GRANT USAGE, SELECT, UPDATE" in text

    assert (
        "ALTER DEFAULT PRIVILEGES"
        in text
    )


def test_api_service_does_not_load_migration_secret() -> None:
    text = API_UNIT.read_text(encoding="utf-8")

    assert (
        "EnvironmentFile=/etc/dacqua-dolce/backend.env"
        in text
    )
    assert "migration.env" not in text
