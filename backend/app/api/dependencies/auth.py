from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db.session import get_db
from app.models.identity import (
    RoleName,
    User,
    UserSession,
    UserStatus,
)
from app.services.mfa import (
    user_requires_mfa,
)
from app.services.sessions import (
    hash_session_token,
)

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]

settings = get_settings()


def get_current_session(
    db: DatabaseSession,
    session_token: Annotated[
        str | None,
        Cookie(
            alias=(
                settings.session_cookie_name
            ),
        ),
    ] = None,
) -> UserSession:
    if session_token is None:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Authentication required.",
        )

    token_hash = hash_session_token(
        session_token
    )
    now = datetime.now(UTC)

    session_record = db.scalar(
        select(UserSession)
        .options(
            selectinload(
                UserSession.user
            ).selectinload(
                User.roles
            )
        )
        .where(
            UserSession.token_hash
            == token_hash,
            UserSession.revoked_at.is_(
                None
            ),
            UserSession.expires_at > now,
        )
    )

    if (
        session_record is None
        or session_record.user.status
        != UserStatus.active
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Authentication required.",
        )

    session_record.last_seen_at = now
    db.commit()

    return session_record


CurrentSession = Annotated[
    UserSession,
    Depends(get_current_session),
]


def get_current_user(
    current_session: CurrentSession,
) -> User:
    user = current_session.user

    if (
        user_requires_mfa(user)
        and current_session.mfa_verified_at
        is None
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="MFA verification required.",
        )

    return user


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]


CUSTOMER_ROLES = frozenset(
    {
        RoleName.customer,
    }
)

OPERATIONS_ROLES = frozenset(
    {
        RoleName.employee,
        RoleName.manager,
        RoleName.administrator,
        RoleName.developer,
    }
)

PRIVILEGED_OPERATIONS_ROLES = (
    frozenset(
        {
            RoleName.manager,
            RoleName.administrator,
            RoleName.developer,
        }
    )
)

ADMINISTRATION_ROLES = frozenset(
    {
        RoleName.administrator,
        RoleName.developer,
    }
)

DEVELOPER_ROLES = frozenset(
    {
        RoleName.developer,
    }
)


def require_roles(
    *allowed_roles: str | RoleName,
) -> Callable[[User], User]:
    normalized_roles = {
        (
            role
            if isinstance(
                role,
                RoleName,
            )
            else RoleName(role)
        )
        for role in allowed_roles
    }

    def dependency(
        current_user: CurrentUser,
    ) -> User:
        user_roles = {
            assignment.role
            for assignment
            in current_user.roles
        }

        if not user_roles.intersection(
            normalized_roles
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Insufficient permissions."
                ),
            )

        return current_user

    return dependency
