import uuid
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app.models.identity import (
    RoleName,
    UserRole,
)
from app.services import (
    account_administration,
)


class ScalarResult:
    def __init__(
        self,
        values: list[UserRole],
    ) -> None:
        self.values = values

    def all(self) -> list[UserRole]:
        return self.values


class RoleDatabase:
    def __init__(
        self,
        assignments: list[UserRole],
        *,
        other_administrators: int = 1,
    ) -> None:
        self.assignments = assignments
        self.other_administrators = (
            other_administrators
        )
        self.added: list[object] = []
        self.deleted: list[object] = []
        self.committed = False

    def scalars(
        self,
        statement: object,
    ) -> ScalarResult:
        return ScalarResult(
            self.assignments
        )

    def scalar(
        self,
        statement: object,
    ) -> int:
        return self.other_administrators

    def add(
        self,
        value: object,
    ) -> None:
        self.added.append(value)

    def delete(
        self,
        value: object,
    ) -> None:
        self.deleted.append(value)

    def commit(self) -> None:
        self.committed = True


def assignment(
    user_id: uuid.UUID,
    role: RoleName,
) -> UserRole:
    return UserRole(
        user_id=user_id,
        role=role,
    )


def test_role_update_preserves_customer_role(
    monkeypatch: Any,
) -> None:
    actor_id = uuid.uuid4()
    target_id = uuid.uuid4()

    customer = assignment(
        target_id,
        RoleName.customer,
    )
    employee = assignment(
        target_id,
        RoleName.employee,
    )

    database = RoleDatabase(
        [customer, employee]
    )

    audit_events: list[dict[str, object]] = []

    monkeypatch.setattr(
        account_administration,
        "record_audit_event",
        lambda db, **kwargs: (
            audit_events.append(kwargs)
        ),
    )

    account_administration.replace_web_managed_roles(
        database,  # type: ignore[arg-type]
        actor=SimpleNamespace(
            id=actor_id,
        ),  # type: ignore[arg-type]
        target=SimpleNamespace(
            id=target_id,
            email="staff@example.test",
        ),  # type: ignore[arg-type]
        desired_roles={
            RoleName.administrator,
        },
    )

    assert employee in database.deleted
    assert customer not in database.deleted

    added_roles = {
        item.role
        for item in database.added
        if isinstance(
            item,
            UserRole,
        )
    }

    assert added_roles == {
        RoleName.administrator,
    }
    assert database.committed is True

    assert audit_events[0][
        "metadata"
    ]["previous_roles"] == [
        "employee"
    ]
    assert audit_events[0][
        "metadata"
    ]["new_roles"] == [
        "administrator"
    ]


def test_admin_cannot_remove_own_admin_role() -> None:
    user_id = uuid.uuid4()

    database = RoleDatabase(
        [
            assignment(
                user_id,
                RoleName.administrator,
            )
        ]
    )

    user = SimpleNamespace(
        id=user_id,
        email="admin@example.test",
    )

    with pytest.raises(
        HTTPException,
    ) as exc:
        account_administration.replace_web_managed_roles(
            database,  # type: ignore[arg-type]
            actor=user,  # type: ignore[arg-type]
            target=user,  # type: ignore[arg-type]
            desired_roles=set(),
        )

    assert exc.value.status_code == 409
    assert database.committed is False


def test_final_admin_role_cannot_be_removed() -> None:
    actor_id = uuid.uuid4()
    target_id = uuid.uuid4()

    database = RoleDatabase(
        [
            assignment(
                target_id,
                RoleName.administrator,
            )
        ],
        other_administrators=0,
    )

    with pytest.raises(
        HTTPException,
    ) as exc:
        account_administration.replace_web_managed_roles(
            database,  # type: ignore[arg-type]
            actor=SimpleNamespace(
                id=actor_id,
            ),  # type: ignore[arg-type]
            target=SimpleNamespace(
                id=target_id,
                email="admin@example.test",
            ),  # type: ignore[arg-type]
            desired_roles=set(),
        )

    assert exc.value.status_code == 409
    assert database.committed is False


def test_developer_role_is_not_web_managed() -> None:
    actor_id = uuid.uuid4()
    target_id = uuid.uuid4()

    database = RoleDatabase(
        [
            assignment(
                target_id,
                RoleName.developer,
            )
        ]
    )

    with pytest.raises(
        HTTPException,
    ) as exc:
        account_administration.replace_web_managed_roles(
            database,  # type: ignore[arg-type]
            actor=SimpleNamespace(
                id=actor_id,
            ),  # type: ignore[arg-type]
            target=SimpleNamespace(
                id=target_id,
                email="developer@example.test",
            ),  # type: ignore[arg-type]
            desired_roles={
                RoleName.employee,
            },
        )

    assert exc.value.status_code == 409
    assert database.committed is False
