#!/usr/bin/env python3
"""Create or verify a deterministic manifest for a staged D'Acqua Dolce release tree."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import NoReturn

MANIFEST_NAME = ".dacqua-release-manifest.json"
REVISION_NAME = ".dacqua-release-revision"
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")


def fail(message: str) -> NoReturn:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def hash_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def describe_path(path: Path) -> dict[str, str]:
    if path.is_symlink():
        target = os.readlink(path)
        return {
            "kind": "symlink",
            "sha256": hash_bytes(target.encode("utf-8")),
        }

    if path.is_file():
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return {
            "kind": "file",
            "sha256": digest.hexdigest(),
        }

    fail(f"unsupported staged path type: {path}")


def collect_entries(root: Path) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}

    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()

        if rel == MANIFEST_NAME:
            continue

        if path.is_dir() and not path.is_symlink():
            continue

        entries[rel] = describe_path(path)

    return entries


def validate_revision(revision: str) -> str:
    revision = revision.strip().lower()
    if not REVISION_RE.fullmatch(revision):
        fail("revision must be a 40-character lowercase Git SHA-1")
    return revision


def write_manifest(root: Path, revision: str) -> None:
    revision = validate_revision(revision)
    revision_path = root / REVISION_NAME
    manifest_path = root / MANIFEST_NAME

    revision_path.write_text(f"{revision}\n", encoding="utf-8")
    entries = collect_entries(root)

    payload = {
        "schema": 1,
        "revision": revision,
        "file_count": len(entries),
        "files": entries,
    }

    temporary = manifest_path.with_name(f"{MANIFEST_NAME}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(manifest_path)

    verify_manifest(root, revision)
    print(f"PASS: wrote staged-source manifest for revision {revision}")
    print(f"Files tracked: {len(entries)}")


def verify_manifest(root: Path, expected_revision: str | None = None) -> None:
    manifest_path = root / MANIFEST_NAME
    revision_path = root / REVISION_NAME

    if not manifest_path.is_file():
        fail(f"staged-source manifest is missing: {manifest_path}")
    if not revision_path.is_file():
        fail(f"staged-source revision marker is missing: {revision_path}")

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read staged-source manifest: {exc}")

    if payload.get("schema") != 1:
        fail("unsupported staged-source manifest schema")

    manifest_revision = validate_revision(str(payload.get("revision", "")))
    marker_revision = validate_revision(revision_path.read_text(encoding="utf-8"))

    if manifest_revision != marker_revision:
        fail("revision marker does not match manifest revision")

    if expected_revision is not None:
        expected_revision = validate_revision(expected_revision)
        if manifest_revision != expected_revision:
            fail(
                "staged revision does not match requested revision: "
                f"expected {expected_revision}, got {manifest_revision}"
            )

    expected_files = payload.get("files")
    if not isinstance(expected_files, dict):
        fail("manifest files field is invalid")

    if payload.get("file_count") != len(expected_files):
        fail("manifest file_count does not match manifest files")

    actual_files = collect_entries(root)

    expected_names = set(expected_files)
    actual_names = set(actual_files)

    missing = sorted(expected_names - actual_names)
    unexpected = sorted(actual_names - expected_names)

    if missing:
        fail(f"staged source is missing manifest files: {', '.join(missing[:10])}")
    if unexpected:
        fail(f"staged source contains unexpected files: {', '.join(unexpected[:10])}")

    for rel in sorted(expected_files):
        expected = expected_files[rel]
        actual = actual_files[rel]
        if expected != actual:
            fail(f"staged source hash/type mismatch: {rel}")

    print(f"PASS: staged source matches revision {manifest_revision}")
    print(f"Files verified: {len(actual_files)}")


def usage() -> None:
    print(
        "usage:\n"
        "  verify_staged_source.py write ROOT 40_CHAR_REVISION\n"
        "  verify_staged_source.py verify ROOT [40_CHAR_REVISION]",
        file=sys.stderr,
    )


def main() -> None:
    if len(sys.argv) < 3:
        usage()
        raise SystemExit(2)

    mode = sys.argv[1]
    root = Path(sys.argv[2]).expanduser().resolve()

    if not root.is_dir():
        fail(f"staged source root is not a directory: {root}")

    if mode == "write":
        if len(sys.argv) != 4:
            usage()
            raise SystemExit(2)
        write_manifest(root, sys.argv[3])
        return

    if mode == "verify":
        if len(sys.argv) not in {3, 4}:
            usage()
            raise SystemExit(2)
        expected_revision = sys.argv[3] if len(sys.argv) == 4 else None
        verify_manifest(root, expected_revision)
        return

    usage()
    raise SystemExit(2)


if __name__ == "__main__":
    main()
