import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.identity import (
    RoleName,
    User,
    UserRole,
    UserSession,
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
    if len(desired_roles) > 1:
        raise ValueError("Staff accounts may have only one web-managed staff role.")

    if RoleName.manager in desired_roles:
        raise ValueError("Manager role is legacy and cannot be newly assigned.")

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


def set_web_managed_account_status(
    db: Session,
    *,
    actor: User,
    target: User,
    desired_status: UserStatus,
) -> None:
    if desired_status not in {
        UserStatus.active,
        UserStatus.disabled,
    }:
        raise ValueError(
            "Web administration may only activate or disable accounts."
        )

    target_roles = {
        assignment.role
        for assignment in target.roles
    }

    if RoleName.developer in target_roles:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Developer account status is managed locally and cannot "
                "be changed in the web console."
            ),
        )

    if desired_status == UserStatus.disabled and actor.id == target.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You cannot disable your own account.",
        )

    if target.status not in {
        UserStatus.active,
        UserStatus.disabled,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Locked accounts are managed by the authentication "
                "lockout workflow and cannot be changed here."
            ),
        )

    if target.status == desired_status:
        return

    if (
        desired_status == UserStatus.disabled
        and RoleName.administrator in target_roles
    ):
        other_administrators = (
            db.scalar(
                select(func.count())
                .select_from(UserRole)
                .join(
                    User,
                    User.id == UserRole.user_id,
                )
                .where(
                    UserRole.role == RoleName.administrator,
                    UserRole.user_id != target.id,
                    User.status == UserStatus.active,
                )
            )
            or 0
        )

        if other_administrators == 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The final active administrator cannot be disabled.",
            )

    previous_status = target.status
    target.status = desired_status

    revoked_count = 0
    if desired_status == UserStatus.disabled:
        now = datetime.now(UTC)
        sessions = db.scalars(
            select(UserSession).where(
                UserSession.user_id == target.id,
                UserSession.revoked_at.is_(None),
            )
        ).all()

        for session_record in sessions:
            session_record.revoked_at = now

        revoked_count = len(sessions)

    record_audit_event(
        db,
        action="identity.account_status_changed",
        entity_type="user",
        entity_id=str(target.id),
        actor_user_id=actor.id,
        metadata={
            "target_email": target.email,
            "previous_status": previous_status.value,
            "new_status": desired_status.value,
            "revoked_session_count": revoked_count,
            "source": "web_administration",
        },
    )

    db.commit()
