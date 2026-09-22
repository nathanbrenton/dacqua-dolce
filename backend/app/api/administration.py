import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.dependencies.auth import (
    CurrentUser,
    DatabaseSession,
)
from app.models.identity import (
    User,
    UserMfa,
)
from app.schemas.administration import (
    AdministrationAccountRead,
    AdministrationRolesUpdate,
)
from app.services.account_administration import (
    load_user_with_roles,
    replace_web_managed_roles,
)
from app.services.mfa import user_requires_mfa
from app.services.operations_access import (
    require_administration,
)

router = APIRouter(
    prefix="/administration",
    tags=["administration"],
)


def administration_account_read(
    db: DatabaseSession,
    *,
    user: User,
) -> AdministrationAccountRead:
    mfa = db.get(
        UserMfa,
        user.id,
    )

    return AdministrationAccountRead(
        id=str(user.id),
        email=user.email,
        status=user.status.value,
        roles=sorted(
            assignment.role.value
            for assignment in user.roles
        ),
        email_verified=(
            user.email_verified_at
            is not None
        ),
        mfa_required=(
            user_requires_mfa(user)
        ),
        mfa_enrolled=(
            mfa is not None
            and mfa.enabled_at is not None
        ),
        created_at=(
            user.created_at.isoformat()
        ),
        last_login_at=(
            user.last_login_at.isoformat()
            if user.last_login_at
            is not None
            else None
        ),
    )


@router.get(
    "/accounts",
    response_model=list[
        AdministrationAccountRead
    ],
)
def list_accounts(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> list[AdministrationAccountRead]:
    require_administration(
        db,
        user=current_user,
    )

    users = db.scalars(
        select(User)
        .options(
            selectinload(User.roles)
        )
        .order_by(
            User.created_at.desc(),
            User.email,
        )
        .limit(1000)
    ).all()

    return [
        administration_account_read(
            db,
            user=user,
        )
        for user in users
    ]


@router.put(
    "/accounts/{user_id}/roles",
    response_model=AdministrationAccountRead,
)
def replace_account_roles(
    user_id: uuid.UUID,
    payload: AdministrationRolesUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> AdministrationAccountRead:
    require_administration(
        db,
        user=current_user,
    )

    target = load_user_with_roles(
        db,
        user_id=user_id,
    )

    if target is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Account not found.",
        )

    replace_web_managed_roles(
        db,
        actor=current_user,
        target=target,
        desired_roles=set(
            payload.roles
        ),
    )

    refreshed = load_user_with_roles(
        db,
        user_id=user_id,
    )

    if refreshed is None:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Account refresh failed."
            ),
        )

    return administration_account_read(
        db,
        user=refreshed,
    )
