import argparse
from datetime import date

from app.core.email_config import get_email_runtime_settings
from app.db.session import SessionLocal
from app.services.maintenance_reminders import (
    dispatch_maintenance_reminder,
    due_maintenance_reminders,
)


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Date must use YYYY-MM-DD."
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Preview or send due D'Acqua Dolce maintenance reminders."
        )
    )
    parser.add_argument(
        "--as-of",
        type=parse_date,
        default=date.today(),
        help="Evaluate reminders due on or before this date.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum reminder candidates to process.",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help=(
            "Actually send through the configured provider. "
            "Without this flag the command is read-only."
        ),
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.limit < 1 or args.limit > 1000:
        parser.error("--limit must be between 1 and 1000.")

    settings = get_email_runtime_settings()

    if args.send and (
        settings.email_provider != "postmark"
        or settings.postmark_token_value is None
    ):
        parser.error(
            "--send requires the Postmark provider and configured server token."
        )

    with SessionLocal() as db:
        candidates = due_maintenance_reminders(
            db,
            as_of=args.as_of,
            limit=args.limit,
        )

        print(
            f"Due reminder candidates through {args.as_of.isoformat()}: "
            f"{len(candidates)}"
        )

        for candidate in candidates:
            print(
                " | ".join(
                    (
                        candidate.recipient,
                        candidate.equipment_name,
                        candidate.related_product_name,
                        candidate.reminder_kind.value,
                        candidate.due_on.isoformat(),
                    )
                )
            )

        if not args.send:
            print("DRY RUN: no email or database writes were performed.")
            return 0

        sent = 0
        failed = 0
        suppressed = 0

        for candidate in candidates:
            reminder = dispatch_maintenance_reminder(
                db,
                candidate=candidate,
                settings=settings,
            )
            if reminder.status.value == "sent":
                sent += 1
            elif reminder.status.value == "suppressed":
                suppressed += 1
            else:
                failed += 1

        db.commit()

    print(
        f"Reminder run complete: sent={sent}, "
        f"failed={failed}, suppressed={suppressed}."
    )

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
