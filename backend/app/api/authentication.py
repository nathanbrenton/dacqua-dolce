from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import CurrentUser
from app.core.config import Settings, get_settings
from app.core.privacy import privacy_safe_identifier
from app.core.security import (
    clear_csrf_cookie,
    issue_csrf_cookie,
)
from app.db.session import get_db
from app.models.identity import (
    RoleName,
    User,
    UserRole,
    UserSession,
)
from app.schemas.authentication import (
    AccountRegistrationRequest,
    AuthenticationStatus,
    LoginRequest,
    SessionListResponse,
    UserSessionRead,
)
from app.services.audit import record_audit_event
from app.services.auth_rate_limit import (
    AuthenticationRateLimiter,
)
from app.services.authentication import (
    attach_password,
    authenticate_user,
)
from app.services.passwords import hash_password
from app.services.sessions import (
    build_session,
    generate_session_token,
    hash_session_token,
)

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]

SettingsDependency = Annotated[
    Settings,
    Depends(get_settings),
]

settings_snapshot = get_settings()

login_ip_limiter = AuthenticationRateLimiter(
    window_seconds=(settings_snapshot.auth_rate_limit_window_seconds),
    max_attempts=(settings_snapshot.auth_rate_limit_ip_attempts),
)

login_account_limiter = AuthenticationRateLimiter(
    window_seconds=(settings_snapshot.auth_rate_limit_window_seconds),
    max_attempts=(settings_snapshot.auth_rate_limit_account_attempts),
)

registration_ip_limiter = AuthenticationRateLimiter(
    window_seconds=(settings_snapshot.auth_rate_limit_window_seconds),
    max_attempts=(settings_snapshot.registration_rate_limit_ip_attempts),
)


def request_ip(
    request: Request,
) -> str | None:
    if request.client is None:
        return None

    return request.client.host


def bounded_user_agent(
    request: Request,
    settings: Settings,
) -> str | None:
    value = request.headers.get("user-agent")

    if value is None:
        return None

    return value.replace("\r", " ").replace("\n", " ")[: settings.request_user_agent_max_length]


def set_session_cookie(
    response: Response,
    settings: Settings,
    token: str,
) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        max_age=settings.session_max_age_seconds,
        path="/",
    )


def clear_session_cookie(
    response: Response,
    settings: Settings,
) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite=settings.session_cookie_samesite,
    )


def rate_limit_or_reject(
    *,
    limiter: AuthenticationRateLimiter,
    key: str,
) -> None:
    decision = limiter.check_and_record(key)

    if not decision.allowed:
        raise HTTPException(
            status_code=(status.HTTP_429_TOO_MANY_REQUESTS),
            detail=("Too many authentication attempts. Try again later."),
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )


@router.get("/csrf")
def csrf_token(
    response: Response,
    settings: SettingsDependency,
) -> dict[str, str]:
    token = issue_csrf_cookie(
        response,
        settings,
    )

    return {"csrf_token": token}


@router.post(
    "/register",
    response_model=AuthenticationStatus,
    status_code=status.HTTP_201_CREATED,
)
def register_account(
    payload: AccountRegistrationRequest,
    request: Request,
    response: Response,
    db: DatabaseSession,
    settings: SettingsDependency,
) -> AuthenticationStatus:
    ip = request_ip(request) or "unknown"

    rate_limit_or_reject(
        limiter=registration_ip_limiter,
        key=f"registration:{ip}",
    )

    existing_user = db.scalar(select(User).where(User.email == payload.email))

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("An account with that email already exists."),
        )

    user = User(email=payload.email)

    attach_password(
        user,
        hash_password(payload.password),
    )

    user.roles.append(UserRole(role=RoleName.customer))

    db.add(user)
    db.flush()

    token = generate_session_token()

    db.add(
        build_session(
            user_id=user.id,
            token=token,
            max_age_seconds=(settings.session_max_age_seconds),
            ip_address=request_ip(request),
            user_agent=bounded_user_agent(
                request,
                settings,
            ),
        )
    )

    record_audit_event(
        db,
        action="account.registered",
        entity_type="user",
        entity_id=str(user.id),
        actor_user_id=user.id,
        ip_address=request_ip(request),
        user_agent=bounded_user_agent(
            request,
            settings,
        ),
    )

    db.commit()

    set_session_cookie(
        response,
        settings,
        token,
    )

    issue_csrf_cookie(
        response,
        settings,
    )

    return AuthenticationStatus(
        authenticated=True,
        email=user.email,
        roles=[RoleName.customer.value],
    )


@router.post(
    "/login",
    response_model=AuthenticationStatus,
)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: DatabaseSession,
    settings: SettingsDependency,
) -> AuthenticationStatus:
    ip = request_ip(request) or "unknown"

    account_key = AuthenticationRateLimiter.email_key(payload.email)

    rate_limit_or_reject(
        limiter=login_ip_limiter,
        key=f"login-ip:{ip}",
    )

    rate_limit_or_reject(
        limiter=login_account_limiter,
        key=f"login-account:{account_key}",
    )

    user = authenticate_user(
        db,
        email=payload.email,
        password=payload.password,
    )

    if user is None:
        record_audit_event(
            db,
            action="authentication.failed",
            entity_type="user",
            metadata={"account_identifier": (privacy_safe_identifier(payload.email))},
            ip_address=request_ip(request),
            user_agent=bounded_user_agent(
                request,
                settings,
            ),
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    login_account_limiter.clear(f"login-account:{account_key}")

    active_sessions = db.scalars(
        select(UserSession)
        .where(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > datetime.now(UTC),
        )
        .order_by(UserSession.created_at.desc())
    ).all()

    keep_existing = max(
        0,
        settings.max_active_sessions_per_user - 1,
    )

    for stale_session in active_sessions[keep_existing:]:
        stale_session.revoked_at = datetime.now(UTC)

    token = generate_session_token()

    db.add(
        build_session(
            user_id=user.id,
            token=token,
            max_age_seconds=(settings.session_max_age_seconds),
            ip_address=request_ip(request),
            user_agent=bounded_user_agent(
                request,
                settings,
            ),
        )
    )

    record_audit_event(
        db,
        action="authentication.succeeded",
        entity_type="user",
        entity_id=str(user.id),
        actor_user_id=user.id,
        ip_address=request_ip(request),
        user_agent=bounded_user_agent(
            request,
            settings,
        ),
    )

    db.commit()

    set_session_cookie(
        response,
        settings,
        token,
    )

    issue_csrf_cookie(
        response,
        settings,
    )

    return AuthenticationStatus(
        authenticated=True,
        email=user.email,
        roles=[assignment.role.value for assignment in user.roles],
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    request: Request,
    response: Response,
    db: DatabaseSession,
    settings: SettingsDependency,
) -> None:
    token = request.cookies.get(settings.session_cookie_name)

    if token is not None:
        session_record = db.scalar(
            select(UserSession).where(
                UserSession.token_hash == hash_session_token(token),
                UserSession.revoked_at.is_(None),
            )
        )

        if session_record is not None:
            session_record.revoked_at = datetime.now(UTC)

            record_audit_event(
                db,
                action="authentication.logout",
                entity_type="user_session",
                entity_id=str(session_record.id),
                actor_user_id=(session_record.user_id),
                ip_address=request_ip(request),
                user_agent=bounded_user_agent(
                    request,
                    settings,
                ),
            )

            db.commit()

    clear_session_cookie(
        response,
        settings,
    )

    clear_csrf_cookie(
        response,
        settings,
    )


@router.get(
    "/me",
    response_model=AuthenticationStatus,
)
def current_account(
    current_user: CurrentUser,
) -> AuthenticationStatus:
    return AuthenticationStatus(
        authenticated=True,
        email=current_user.email,
        roles=[assignment.role.value for assignment in current_user.roles],
    )


@router.get(
    "/sessions",
    response_model=SessionListResponse,
)
def list_sessions(
    request: Request,
    db: DatabaseSession,
    settings: SettingsDependency,
    current_user: CurrentUser,
) -> SessionListResponse:
    active = db.scalars(
        select(UserSession)
        .where(
            UserSession.user_id == current_user.id,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > datetime.now(UTC),
        )
        .order_by(UserSession.created_at.desc())
    ).all()

    current_token = request.cookies.get(settings.session_cookie_name)

    current_hash = hash_session_token(current_token) if current_token is not None else None

    return SessionListResponse(
        sessions=[
            UserSessionRead(
                id=str(session.id),
                created_at=(session.created_at.isoformat()),
                last_seen_at=(
                    session.last_seen_at.isoformat() if session.last_seen_at is not None else None
                ),
                expires_at=(session.expires_at.isoformat()),
                ip_address=session.ip_address,
                user_agent=session.user_agent,
                current=(current_hash is not None and session.token_hash == current_hash),
            )
            for session in active
        ]
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def revoke_session(
    session_id: UUID,
    request: Request,
    response: Response,
    db: DatabaseSession,
    settings: SettingsDependency,
    current_user: CurrentUser,
) -> None:
    session_record = db.scalar(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == current_user.id,
            UserSession.revoked_at.is_(None),
        )
    )

    if session_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    current_token = request.cookies.get(settings.session_cookie_name)

    is_current = current_token is not None and session_record.token_hash == hash_session_token(
        current_token
    )

    session_record.revoked_at = datetime.now(UTC)

    record_audit_event(
        db,
        action="authentication.session_revoked",
        entity_type="user_session",
        entity_id=str(session_record.id),
        actor_user_id=current_user.id,
        ip_address=request_ip(request),
        user_agent=bounded_user_agent(
            request,
            settings,
        ),
    )

    db.commit()

    if is_current:
        clear_session_cookie(
            response,
            settings,
        )

        clear_csrf_cookie(
            response,
            settings,
        )


@router.post(
    "/sessions/revoke-all",
    status_code=status.HTTP_204_NO_CONTENT,
)
def revoke_all_sessions(
    request: Request,
    response: Response,
    db: DatabaseSession,
    settings: SettingsDependency,
    current_user: CurrentUser,
) -> None:
    sessions = db.scalars(
        select(UserSession).where(
            UserSession.user_id == current_user.id,
            UserSession.revoked_at.is_(None),
        )
    ).all()

    now = datetime.now(UTC)

    for session_record in sessions:
        session_record.revoked_at = now

    record_audit_event(
        db,
        action=("authentication.sessions_revoked_all"),
        entity_type="user",
        entity_id=str(current_user.id),
        actor_user_id=current_user.id,
        metadata={"revoked_count": len(sessions)},
        ip_address=request_ip(request),
        user_agent=bounded_user_agent(
            request,
            settings,
        ),
    )

    db.commit()

    clear_session_cookie(
        response,
        settings,
    )

    clear_csrf_cookie(
        response,
        settings,
    )
