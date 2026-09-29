import os
from datetime import UTC, datetime

from sqlalchemy import delete, select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.identity import RoleName, User, UserCredential, UserRole
from app.services.passwords import hash_password

CANONICAL_USERS = (
    ("developer@dacquadolce.test", RoleName.developer, "DACQUA_BOOTSTRAP_DEVELOPER_PASSWORD"),
    ("admin@dacquadolce.test", RoleName.administrator, "DACQUA_BOOTSTRAP_ADMIN_PASSWORD"),
    ("employee@dacquadolce.test", RoleName.employee, "DACQUA_BOOTSTRAP_EMPLOYEE_PASSWORD"),
    ("customer@dacquadolce.test", RoleName.customer, "DACQUA_BOOTSTRAP_CUSTOMER_PASSWORD"),
    (
        "payment-test-customer@dacquadolce.test",
        RoleName.customer,
        "DACQUA_BOOTSTRAP_PAYMENT_TEST_PASSWORD",
    ),
)


def main() -> int:
    settings = get_settings()
    if settings.is_production:
        raise SystemExit("ERROR: dev user bootstrap is forbidden in production.")

    passwords: dict[str, str] = {}
    for _, _, variable in CANONICAL_USERS:
        value = os.environ.get(variable, "")
        if not value:
            raise SystemExit(f"ERROR: {variable} is required.")
        passwords[variable] = value

    with SessionLocal() as db:
        for email, role, variable in CANONICAL_USERS:
            user = db.scalar(select(User).where(User.email == email))
            if user is None:
                user = User(email=email, email_verified_at=datetime.now(UTC))
                db.add(user)
                db.flush()

            if user.credential is None:
                user.credential = UserCredential(password_hash=hash_password(passwords[variable]))
            else:
                user.credential.password_hash = hash_password(passwords[variable])
                user.credential.password_changed_at = datetime.now(UTC)

            db.execute(delete(UserRole).where(UserRole.user_id == user.id))
            db.add(UserRole(user_id=user.id, role=role, assigned_by_user_id=None))

        db.commit()

    print("Canonical dev/test identities are ready; passwords were not printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
