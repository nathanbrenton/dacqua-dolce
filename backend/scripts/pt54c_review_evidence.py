#!/usr/bin/env python3
"""Generate/review local PT54-C3 evidence files without authorizing options."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.services.commercial_evidence_intake import as_json, load_intake, make_template, review_report  # noqa: E402


def external_path(value: str, *, must_exist: bool = False) -> Path:
    path = Path(value).expanduser().resolve()
    if path.is_relative_to(BACKEND.parent.resolve()):
        raise ValueError("Supplier evidence files must stay outside the Git repository")
    if must_exist and not path.is_file():
        raise ValueError(f"Input file not found: {path}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="PT54-C3 local non-authorizing evidence intake")
    actions = parser.add_subparsers(dest="action", required=True)
    template = actions.add_parser("template", help="Make blank external evidence intake JSON")
    template.add_argument("--output", required=True)
    review = actions.add_parser("review", help="Validate supplier evidence; produce staff review report")
    review.add_argument("--input", required=True)
    review.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        if args.action == "template":
            output = external_path(args.output)
            value = make_template()
        else:
            source = external_path(args.input, must_exist=True)
            output = external_path(args.output)
            if source == output:
                raise ValueError("Review output cannot overwrite source evidence")
            value = review_report(load_intake(str(source)))
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as file:  # never overwrite evidence
            file.write(as_json(value))
        print(f"PASS: wrote external {'template' if args.action == 'template' else 'review'}: {output}")
        print("HOLD: no manufacturer fitments, option prices, or catalog SKUs authorized")
        return 0
    except (ValueError, FileExistsError, OSError) as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
