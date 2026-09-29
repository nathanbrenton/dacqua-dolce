from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INIT_SCRIPT = ROOT / "infra" / "postgresql" / "init_local_database.sh"
COMPOSE = ROOT / "infra" / "compose.yaml"
ENV_EXAMPLE = ROOT / "infra" / ".env.example"
REBUILD = ROOT / "scripts" / "rebuild_local_database.sh"


def test_local_bootstrap_separates_dba_migrator_and_runtime() -> None:
    text = INIT_SCRIPT.read_text(encoding="utf-8")
    assert "dacqua_dolce_migrator" in text
    assert "dacqua_dolce_app" in text
    assert "OWNER TO dacqua_dolce_migrator" in text
    assert "REVOKE CREATE ON SCHEMA public FROM dacqua_dolce_app" in text
    assert "GRANT USAGE ON SCHEMA public TO dacqua_dolce_app" in text
    assert "ALTER DEFAULT PRIVILEGES FOR ROLE dacqua_dolce_migrator" in text


def test_local_compose_bootstraps_with_dba_identity() -> None:
    env = ENV_EXAMPLE.read_text(encoding="utf-8")
    compose = COMPOSE.read_text(encoding="utf-8")
    assert "POSTGRES_USER=dacqua_dolce_dba" in env
    assert "DACQUA_DB_MIGRATOR_PASSWORD" in env
    assert "DACQUA_DB_APP_PASSWORD" in env
    assert "init_local_database.sh" in compose


def test_destructive_rebuild_is_guarded_and_backed_up() -> None:
    text = REBUILD.read_text(encoding="utf-8")
    assert "--confirm-destroy-local-data" in text
    assert "pg_dump -Fc" in text
    assert "docker compose down -v" in text
    assert 'POSTGRES_DB" != "dacqua_dolce_dev"' in text
    assert 'POSTGRES_USER" != "dacqua_dolce_dba"' in text
