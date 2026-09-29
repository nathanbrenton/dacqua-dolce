#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    backend_root = repo_root / "backend"

    if not backend_root.is_dir():
        print(f"ERROR: backend directory not found: {backend_root}", file=sys.stderr)
        return 1

    # Application settings load backend/.env relative to the current
    # working directory. Match the established local role launcher.
    os.chdir(backend_root)

    backend_path = str(backend_root)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)

    # Import only after backend/ is the working directory and import root.
    from app.cli.bootstrap_dev_users import main as bootstrap_main

    return bootstrap_main()


if __name__ == "__main__":
    raise SystemExit(main())
