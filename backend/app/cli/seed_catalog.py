import argparse
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.services.catalog_seed import (
    DEFAULT_CATALOG_PATH,
    CatalogSeedError,
    apply_catalog_manifest,
    load_catalog_manifest,
)


def print_result(
    *,
    mode: str,
    source: Path,
    result: object,
) -> None:
    print(f"Catalog source: {source}")
    print(f"Mode: {mode}")
    print()

    for name, value in result.__dict__.items():
        print(f"{name:28} {value}")

    print(f"{'total_changes':28} {result.total_changes}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Plan or apply the canonical D'Acqua Dolce product catalog baseline."
        )
    )
    parser.add_argument(
        "mode",
        choices=(
            "plan",
            "apply",
        ),
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_CATALOG_PATH,
    )
    args = parser.parse_args()

    try:
        data = load_catalog_manifest(args.source)

        settings = get_settings()
        engine = create_engine(
            settings.alembic_database_url,
            pool_pre_ping=True,
        )
        SeedSession = sessionmaker(
            bind=engine,
            autoflush=False,
            expire_on_commit=False,
        )

        with SeedSession() as db:
            result = apply_catalog_manifest(db, data)
            db.flush()

            if args.mode == "apply":
                db.commit()
            else:
                db.rollback()

        print_result(
            mode=args.mode,
            source=args.source,
            result=result,
        )
        return 0

    except (CatalogSeedError, OSError, ValueError) as exc:
        parser.error(str(exc))

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
