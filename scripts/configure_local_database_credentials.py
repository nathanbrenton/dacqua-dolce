#!/usr/bin/env python3
from __future__ import annotations

import argparse
import secrets
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

TARGET_DB = "dacqua_dolce_dev"
TARGET_DBA = "dacqua_dolce_dba"
TARGET_APP = "dacqua_dolce_app"


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def upsert_env(path: Path, updates: dict[str, str], remove: set[str] | None = None) -> None:
    remove = remove or set()
    lines = path.read_text(encoding="utf-8").splitlines()
    seen: set[str] = set()
    out: list[str] = []

    for raw in lines:
        if "=" not in raw or raw.lstrip().startswith("#"):
            out.append(raw)
            continue

        key = raw.split("=", 1)[0].strip()
        if key in remove:
            continue
        if key in updates:
            out.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            out.append(raw)

    for key, value in updates.items():
        if key not in seen:
            out.append(f"{key}={value}")

    path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    path.chmod(0o600)


def validate(root: Path) -> None:
    infra_path = root / "infra/.env"
    backend_path = root / "backend/.env"

    infra = parse_env(infra_path)
    backend = parse_env(backend_path)

    required = {
        "POSTGRES_PASSWORD",
        "DACQUA_DB_MIGRATOR_PASSWORD",
        "DACQUA_DB_APP_PASSWORD",
    }
    missing = sorted(key for key in required if not infra.get(key))
    if missing:
        raise SystemExit("ERROR: missing local database secret key(s): " + ", ".join(missing))

    if infra.get("POSTGRES_DB") != TARGET_DB:
        raise SystemExit("ERROR: POSTGRES_DB is not the expected local development database.")
    if infra.get("POSTGRES_USER") != TARGET_DBA:
        raise SystemExit("ERROR: POSTGRES_USER is not the expected local DBA identity.")

    secrets_seen = [
        infra["POSTGRES_PASSWORD"],
        infra["DACQUA_DB_MIGRATOR_PASSWORD"],
        infra["DACQUA_DB_APP_PASSWORD"],
    ]
    if len(set(secrets_seen)) != 3:
        raise SystemExit("ERROR: local DBA, migrator, and runtime passwords must be distinct.")

    runtime_url = backend.get("DACQUA_DATABASE_URL", "")
    parsed = urlparse(runtime_url)
    if (
        parsed.scheme != "postgresql+psycopg"
        or parsed.username != TARGET_APP
        or parsed.password != infra["DACQUA_DB_APP_PASSWORD"]
        or parsed.hostname != "127.0.0.1"
        or parsed.port != 15432
        or parsed.path != f"/{TARGET_DB}"
    ):
        raise SystemExit("ERROR: backend runtime database URL does not match the local runtime identity.")

    if "DACQUA_MIGRATION_DATABASE_URL" in backend:
        raise SystemExit(
            "ERROR: migrator URL must not be stored in backend/.env; "
            "FastAPI should receive runtime credentials only."
        )

    environment = backend.get("DACQUA_ENVIRONMENT", "development").strip().lower()
    if environment in {"prod", "production"}:
        raise SystemExit("ERROR: refusing local credential workflow for a production backend environment.")

    print("PASS: local database credentials are separated.")
    print("PASS: backend/.env contains runtime database access only.")
    print("PASS: migrator credentials remain outside the FastAPI runtime environment.")
    print("Secrets were not printed.")


def configure(root: Path) -> None:
    infra_path = root / "infra/.env"
    backend_path = root / "backend/.env"

    if not infra_path.is_file() or not backend_path.is_file():
        raise SystemExit("ERROR: expected infra/.env and backend/.env.")

    old_infra = parse_env(infra_path)
    old_backend = parse_env(backend_path)

    if old_infra.get("POSTGRES_DB") not in {None, "", TARGET_DB}:
        raise SystemExit("ERROR: refusing to modify a non-development PostgreSQL database configuration.")

    environment = old_backend.get("DACQUA_ENVIRONMENT", "development").strip().lower()
    if environment in {"prod", "production"}:
        raise SystemExit("ERROR: refusing to modify a production backend environment.")

    backup_root = (
        Path.home()
        / ".dacqua-dolce"
        / "backups"
        / f"pt18-env-{datetime.now().strftime('%Y%m%dT%H%M%S')}"
    )
    backup_root.mkdir(parents=True, exist_ok=False)
    shutil.copy2(infra_path, backup_root / "infra.env")
    shutil.copy2(backend_path, backup_root / "backend.env")
    (backup_root / "infra.env").chmod(0o600)
    (backup_root / "backend.env").chmod(0o600)

    dba_password = secrets.token_hex(32)
    migrator_password = secrets.token_hex(32)
    app_password = secrets.token_hex(32)

    upsert_env(
        infra_path,
        {
            "POSTGRES_DB": TARGET_DB,
            "POSTGRES_USER": TARGET_DBA,
            "POSTGRES_PASSWORD": dba_password,
            "DACQUA_DB_MIGRATOR_PASSWORD": migrator_password,
            "DACQUA_DB_APP_PASSWORD": app_password,
        },
    )

    runtime_url = (
        f"postgresql+psycopg://{TARGET_APP}:{app_password}"
        f"@127.0.0.1:15432/{TARGET_DB}"
    )
    upsert_env(
        backend_path,
        {"DACQUA_DATABASE_URL": runtime_url},
        remove={"DACQUA_MIGRATION_DATABASE_URL"},
    )

    validate(root)
    print(f"Previous env files were backed up under: {backup_root}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Configure separated local D'Acqua Dolce PostgreSQL credentials without printing secrets."
    )
    parser.add_argument("--check", action="store_true", help="Validate existing local credential separation only.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    if not (root / ".git").exists():
        raise SystemExit("ERROR: expected this script inside the D'Acqua Dolce repository.")

    if args.check:
        validate(root)
    else:
        configure(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
