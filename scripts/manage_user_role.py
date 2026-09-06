#!/usr/bin/env python3

import os
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]

    backend_root = repo_root / "backend"

    if not backend_root.is_dir():
        print(
            f"ERROR: backend directory not found: {backend_root}",
            file=sys.stderr,
        )
        return 1

    # Application settings load
    # backend/.env relative to the
    # current working directory.
    os.chdir(backend_root)

    backend_path = str(backend_root)

    if backend_path not in sys.path:
        sys.path.insert(
            0,
            backend_path,
        )

    # Import only after backend/ is
    # the working directory and import
    # root. This keeps configuration
    # loading independent of the
    # invoking shell directory.
    from app.cli.manage_user_role import (
        main as backend_main,
    )

    return backend_main()


if __name__ == "__main__":
    raise SystemExit(main())
