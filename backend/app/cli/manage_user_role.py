import argparse
import sys

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models.identity import (
    RoleName,
    User,
    UserRole,
    UserStatus,
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

    if role == RoleName.manager:
        print(
            "ERROR: manager is a legacy role and cannot be newly assigned.",
            file=sys.stderr,
        )
        return 2

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

        if role == RoleName.developer:
            other_active_developers = (
                db.scalar(
                    select(func.count())
                    .select_from(UserRole)
                    .join(User, User.id == UserRole.user_id)
                    .where(
                        UserRole.role == RoleName.developer,
                        UserRole.user_id != user.id,
                        User.status == UserStatus.active,
                    )
                )
                or 0
            )
            if other_active_developers == 0:
                print(
                    "ERROR: refusing to remove the final active developer role.",
                    file=sys.stderr,
                )
                return 2

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


def set_staff_role(
    *,
    email: str,
    role: RoleName,
    confirm_replace_all_roles: bool,
) -> int:
    normalized = normalized_email(email)

    if not confirm_replace_all_roles:
        print(
            "ERROR: set-staff-role requires --confirm-replace-all-roles.",
            file=sys.stderr,
        )
        return 2

    if role == RoleName.manager:
        print(
            "ERROR: manager is a legacy role and cannot be newly assigned.",
            file=sys.stderr,
        )
        return 2

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == normalized))

        if user is None:
            print(
                f"ERROR: no user found for {normalized}",
                file=sys.stderr,
            )
            return 1

        assignments = db.scalars(
            select(UserRole).where(
                UserRole.user_id == user.id,
            )
        ).all()

        current_roles = {
            assignment.role
            for assignment in assignments
        }

        if current_roles == {role}:
            print(
                f"{normalized} already has exactly one role: {role.value}."
            )
            return 0

        if (
            RoleName.developer in current_roles
            and role != RoleName.developer
        ):
            other_active_developers = (
                db.scalar(
                    select(func.count())
                    .select_from(UserRole)
                    .join(User, User.id == UserRole.user_id)
                    .where(
                        UserRole.role == RoleName.developer,
                        UserRole.user_id != user.id,
                        User.status == UserStatus.active,
                    )
                )
                or 0
            )

            if other_active_developers == 0:
                print(
                    "ERROR: refusing to replace the final active developer role.",
                    file=sys.stderr,
                )
                return 2

        for assignment in assignments:
            db.delete(assignment)

        db.add(
            UserRole(
                user_id=user.id,
                role=role,
                assigned_by_user_id=None,
            )
        )

        record_audit_event(
            db,
            action="identity.roles_replaced",
            entity_type="user",
            entity_id=str(user.id),
            actor_user_id=None,
            metadata={
                "previous_roles": sorted(
                    item.value
                    for item in current_roles
                ),
                "new_roles": [role.value],
                "source": "local_role_cli",
                "mode": "replace_all_roles",
            },
        )

        db.commit()

        print(
            f"Replaced all roles for {normalized}; "
            f"effective role is now {role.value}."
        )

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

    set_parser = subparsers.add_parser(
        "set-staff-role",
        help=(
            "Replace all roles on one existing account "
            "with exactly one staff role."
        ),
    )

    set_parser.add_argument(
        "--email",
        required=True,
    )

    set_parser.add_argument(
        "--role",
        required=True,
        type=role_from_argument,
    )

    set_parser.add_argument(
        "--confirm-replace-all-roles",
        action="store_true",
        help=(
            "Required confirmation that all existing roles, "
            "including customer, will be replaced."
        ),
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

    if args.command == "set-staff-role":
        return set_staff_role(
            email=args.email,
            role=args.role,
            confirm_replace_all_roles=(
                args.confirm_replace_all_roles
            ),
        )

    parser.error("Unknown command.")

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
