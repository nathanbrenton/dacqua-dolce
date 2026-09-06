import argparse
import sys

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.identity import (
    RoleName,
    User,
    UserRole,
)
from app.services.audit import (
    record_audit_event,
)

ASSIGNABLE_ROLES = frozenset(
    {
        RoleName.employee,
        RoleName.manager,
        RoleName.administrator,
        RoleName.developer,
    }
)


def normalized_email(
    value: str,
) -> str:
    return value.strip().lower()


def role_from_argument(
    value: str,
) -> RoleName:
    try:
        role = RoleName(value)
    except ValueError as exc:
        choices = ", ".join(sorted(item.value for item in ASSIGNABLE_ROLES))

        raise argparse.ArgumentTypeError(f"Role must be one of: {choices}") from exc

    if role not in ASSIGNABLE_ROLES:
        raise argparse.ArgumentTypeError(
            "Customer role is assigned "
            "by normal application "
            "workflows and is not "
            "managed by this CLI."
        )

    return role


def list_users() -> int:
    with SessionLocal() as db:
        users = db.scalars(select(User).order_by(User.email)).all()

        if not users:
            print("No users found.")
            return 0

        print(f"{'EMAIL':<42} ROLES")
        print(f"{'-' * 42} {'-' * 36}")

        for user in users:
            roles = db.scalars(
                select(UserRole.role).where(UserRole.user_id == user.id).order_by(UserRole.role)
            ).all()

            role_text = ", ".join(role.value for role in roles)

            print(f"{user.email:<42} {role_text or '-'}")

    return 0


def add_role(
    *,
    email: str,
    role: RoleName,
) -> int:
    normalized = normalized_email(email)

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == normalized))

        if user is None:
            print(
                f"ERROR: no user found for {normalized}",
                file=sys.stderr,
            )
            return 1

        existing = db.scalar(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role == role,
            )
        )

        if existing is not None:
            print(f"{normalized} already has role {role.value}.")
            return 0

        assignment = UserRole(
            user_id=user.id,
            role=role,
            assigned_by_user_id=None,
        )

        db.add(assignment)
        db.flush()

        record_audit_event(
            db,
            action=("identity.role_assigned"),
            entity_type="user",
            entity_id=str(user.id),
            actor_user_id=None,
            metadata={
                "role": role.value,
                "source": ("local_role_cli"),
            },
        )

        db.commit()

        print(f"Granted {role.value} to {normalized}.")

    return 0


def remove_role(
    *,
    email: str,
    role: RoleName,
) -> int:
    normalized = normalized_email(email)

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == normalized))

        if user is None:
            print(
                f"ERROR: no user found for {normalized}",
                file=sys.stderr,
            )
            return 1

        assignment = db.scalar(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role == role,
            )
        )

        if assignment is None:
            print(f"{normalized} does not have role {role.value}.")
            return 0

        db.delete(assignment)

        record_audit_event(
            db,
            action=("identity.role_revoked"),
            entity_type="user",
            entity_id=str(user.id),
            actor_user_id=None,
            metadata={
                "role": role.value,
                "source": ("local_role_cli"),
            },
        )

        db.commit()

        print(f"Revoked {role.value} from {normalized}.")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=("Manage D'Acqua Dolce operations roles for existing users.")
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "list",
        help=("List existing users and roles."),
    )

    add_parser = subparsers.add_parser(
        "add",
        help=("Grant an operations role to an existing user."),
    )

    add_parser.add_argument(
        "--email",
        required=True,
    )

    add_parser.add_argument(
        "--role",
        required=True,
        type=role_from_argument,
    )

    remove_parser = subparsers.add_parser(
        "remove",
        help=("Revoke an operations role from an existing user."),
    )

    remove_parser.add_argument(
        "--email",
        required=True,
    )

    remove_parser.add_argument(
        "--role",
        required=True,
        type=role_from_argument,
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "list":
        return list_users()

    if args.command == "add":
        return add_role(
            email=args.email,
            role=args.role,
        )

    if args.command == "remove":
        return remove_role(
            email=args.email,
            role=args.role,
        )

    parser.error("Unknown command.")

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
