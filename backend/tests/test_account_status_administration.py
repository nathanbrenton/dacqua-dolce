from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app.models.identity import RoleName, UserStatus
from app.services import account_administration


class ScalarRows:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def all(self) -> list[object]:
        return self.values


class StatusDatabase:
    def __init__(
        self,
        sessions: list[object] | None = None,
        *,
        other_administrators: int = 1,
    ) -> None:
        self.sessions = sessions or []
        self.other_administrators = other_administrators
        self.committed = False

    def scalars(self, statement: object) -> ScalarRows:
        return ScalarRows(self.sessions)

    def scalar(self, statement: object) -> int:
        return self.other_administrators

    def commit(self) -> None:
        self.committed = True


def target_user(
    *,
    status: UserStatus = UserStatus.active,
    roles: set[RoleName] | None = None,
) -> SimpleNamespace:
    user_id = uuid.uuid4()
    return SimpleNamespace(
        id=user_id,
        email="staff@example.test",
        status=status,
        roles=[
            SimpleNamespace(role=role)
            for role in (roles or {RoleName.employee})
        ],
    )


def test_disabling_account_revokes_sessions_and_audits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = target_user()
    actor = SimpleNamespace(id=uuid.uuid4())
    sessions = [
        SimpleNamespace(revoked_at=None),
        SimpleNamespace(revoked_at=None),
    ]
    db = StatusDatabase(sessions)
    audit_events: list[dict[str, Any]] = []

    monkeypatch.setattr(
        account_administration,
        "record_audit_event",
        lambda db, **kwargs: audit_events.append(kwargs),
    )

    account_administration.set_web_managed_account_status(
        db,  # type: ignore[arg-type]
        actor=actor,  # type: ignore[arg-type]
        target=target,  # type: ignore[arg-type]
        desired_status=UserStatus.disabled,
    )

    assert target.status == UserStatus.disabled
    assert all(session.revoked_at is not None for session in sessions)
    assert db.committed is True
    assert audit_events[0]["action"] == "identity.account_status_changed"
    assert audit_events[0]["metadata"]["previous_status"] == "active"
    assert audit_events[0]["metadata"]["new_status"] == "disabled"
    assert audit_events[0]["metadata"]["revoked_session_count"] == 2


def test_account_cannot_disable_itself() -> None:
    target = target_user()
    db = StatusDatabase()

    with pytest.raises(HTTPException) as exc:
        account_administration.set_web_managed_account_status(
            db,  # type: ignore[arg-type]
            actor=target,  # type: ignore[arg-type]
            target=target,  # type: ignore[arg-type]
            desired_status=UserStatus.disabled,
        )

    assert exc.value.status_code == 409
    assert target.status == UserStatus.active
    assert db.committed is False


def test_final_active_administrator_cannot_be_disabled() -> None:
    target = target_user(roles={RoleName.administrator})
    actor = SimpleNamespace(id=uuid.uuid4())
    db = StatusDatabase(other_administrators=0)

    with pytest.raises(HTTPException) as exc:
        account_administration.set_web_managed_account_status(
            db,  # type: ignore[arg-type]
            actor=actor,  # type: ignore[arg-type]
            target=target,  # type: ignore[arg-type]
            desired_status=UserStatus.disabled,
        )

    assert exc.value.status_code == 409
    assert target.status == UserStatus.active
    assert db.committed is False


def test_disabled_account_can_be_reenabled_without_deleting_roles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = target_user(
        status=UserStatus.disabled,
        roles={RoleName.employee},
    )
    actor = SimpleNamespace(id=uuid.uuid4())
    db = StatusDatabase()

    monkeypatch.setattr(
        account_administration,
        "record_audit_event",
        lambda db, **kwargs: None,
    )

    account_administration.set_web_managed_account_status(
        db,  # type: ignore[arg-type]
        actor=actor,  # type: ignore[arg-type]
        target=target,  # type: ignore[arg-type]
        desired_status=UserStatus.active,
    )

    assert target.status == UserStatus.active
    assert [assignment.role for assignment in target.roles] == [RoleName.employee]
    assert db.committed is True


def test_developer_account_status_is_local_only() -> None:
    target = target_user(roles={RoleName.developer})
    actor = SimpleNamespace(id=uuid.uuid4())
    db = StatusDatabase()

    with pytest.raises(HTTPException) as exc:
        account_administration.set_web_managed_account_status(
            db,  # type: ignore[arg-type]
            actor=actor,  # type: ignore[arg-type]
            target=target,  # type: ignore[arg-type]
            desired_status=UserStatus.disabled,
        )

    assert exc.value.status_code == 409
    assert target.status == UserStatus.active
    assert db.committed is False


def test_locked_account_status_is_left_to_lockout_workflow() -> None:
    target = target_user(status=UserStatus.locked)
    actor = SimpleNamespace(id=uuid.uuid4())
    db = StatusDatabase()

    with pytest.raises(HTTPException) as exc:
        account_administration.set_web_managed_account_status(
            db,  # type: ignore[arg-type]
            actor=actor,  # type: ignore[arg-type]
            target=target,  # type: ignore[arg-type]
            desired_status=UserStatus.active,
        )

    assert exc.value.status_code == 409
    assert target.status == UserStatus.locked
    assert db.committed is False
