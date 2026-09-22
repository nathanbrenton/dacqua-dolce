import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.identity import (
    RoleName,
    User,
    UserRole,
    UserStatus,
)
from app.schemas.administration import (
    WEB_MANAGED_OPERATIONS_ROLES,
)
from app.services.audit import (
    record_audit_event,
)


def replace_web_managed_roles(
    db: Session,
    *,
    actor: User,
    target: User,
    desired_roles: set[RoleName],
) -> None:
    if (
        desired_roles
        - WEB_MANAGED_OPERATIONS_ROLES
    ):
        raise ValueError(
            "Unexpected web-managed role."
        )

    assignments = db.scalars(
        select(UserRole).where(
            UserRole.user_id == target.id
        )
    ).all()

    current_roles = {
        assignment.role
        for assignment in assignments
    }

    if RoleName.developer in current_roles:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Developer account roles are "
                "managed locally and cannot "
                "be changed in the web console."
            ),
        )

    current_managed = (
        current_roles
        & WEB_MANAGED_OPERATIONS_ROLES
    )

    removing_administrator = (
        RoleName.administrator
        in current_managed
        and RoleName.administrator
        not in desired_roles
    )

    if (
        removing_administrator
        and actor.id == target.id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "You cannot remove your own "
                "administrator role."
            ),
        )

    if removing_administrator:
        other_administrators = (
            db.scalar(
                select(func.count())
                .select_from(UserRole)
                .join(
                    User,
                    User.id == UserRole.user_id,
                )
                .where(
                    UserRole.role
                    == RoleName.administrator,
                    UserRole.user_id
                    != target.id,
                    User.status
                    == UserStatus.active,
                )
            )
            or 0
        )

        if other_administrators == 0:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "The final administrator "
                    "role cannot be removed."
                ),
            )

    by_role = {
        assignment.role: assignment
        for assignment in assignments
        if assignment.role
        in WEB_MANAGED_OPERATIONS_ROLES
    }

    for role in (
        current_managed
        - desired_roles
    ):
        db.delete(by_role[role])

    for role in (
        desired_roles
        - current_managed
    ):
        db.add(
            UserRole(
                user_id=target.id,
                role=role,
                assigned_by_user_id=(
                    actor.id
                ),
            )
        )

    record_audit_event(
        db,
        action=(
            "identity.operations_roles_changed"
        ),
        entity_type="user",
        entity_id=str(target.id),
        actor_user_id=actor.id,
        metadata={
            "target_email": target.email,
            "previous_roles": sorted(
                role.value
                for role in current_managed
            ),
            "new_roles": sorted(
                role.value
                for role in desired_roles
            ),
            "source": "web_administration",
        },
    )

    db.commit()


def load_user_with_roles(
    db: Session,
    *,
    user_id: uuid.UUID,
) -> User | None:
    return db.scalar(
        select(User)
        .options(
            selectinload(User.roles)
        )
        .where(
            User.id == user_id
        )
    )
