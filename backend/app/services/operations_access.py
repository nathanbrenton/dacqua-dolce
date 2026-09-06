from collections.abc import Iterable

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.identity import (
    RoleName,
    User,
    UserRole,
)

OPERATIONS_ROLES = frozenset(
    {
        RoleName.employee,
        RoleName.manager,
        RoleName.administrator,
        RoleName.developer,
    }
)

PRIVILEGED_OPERATIONS_ROLES = frozenset(
    {
        RoleName.manager,
        RoleName.administrator,
        RoleName.developer,
    }
)


def user_role_names(
    db: Session,
    *,
    user_id: object,
) -> set[RoleName]:
    return set(db.scalars(select(UserRole.role).where(UserRole.user_id == user_id)).all())


def require_any_role(
    db: Session,
    *,
    user: User,
    allowed_roles: Iterable[RoleName],
) -> set[RoleName]:
    allowed = set(allowed_roles)
    actual = user_role_names(
        db,
        user_id=user.id,
    )

    if actual.isdisjoint(allowed):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )

    return actual


def require_operations(
    db: Session,
    *,
    user: User,
) -> set[RoleName]:
    return require_any_role(
        db,
        user=user,
        allowed_roles=OPERATIONS_ROLES,
    )


def require_privileged_operations(
    db: Session,
    *,
    user: User,
) -> set[RoleName]:
    return require_any_role(
        db,
        user=user,
        allowed_roles=PRIVILEGED_OPERATIONS_ROLES,
    )
