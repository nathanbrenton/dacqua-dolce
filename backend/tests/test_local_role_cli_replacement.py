import uuid
from types import SimpleNamespace
from typing import Any

from app.cli import manage_user_role
from app.models.identity import RoleName, UserRole


class ScalarResult:
    def __init__(self, values: list[UserRole]) -> None:
        self.values = values

    def all(self) -> list[UserRole]:
        return self.values


class RoleDatabase:
    def __init__(
        self,
        *,
        user: object,
        assignments: list[UserRole],
        other_active_developers: int = 1,
    ) -> None:
        self.user = user
        self.assignments = assignments
        self.other_active_developers = other_active_developers
        self.scalar_calls = 0
        self.added: list[object] = []
        self.deleted: list[object] = []
        self.committed = False

    def __enter__(self) -> "RoleDatabase":
        return self

    def __exit__(
        self,
        exc_type: object,
        exc: object,
        traceback: object,
    ) -> None:
        return None

    def scalar(self, statement: object) -> object:
        self.scalar_calls += 1
        if self.scalar_calls == 1:
            return self.user
        return self.other_active_developers

    def scalars(self, statement: object) -> ScalarResult:
        return ScalarResult(self.assignments)

    def add(self, value: object) -> None:
        self.added.append(value)

    def delete(self, value: object) -> None:
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


def test_set_staff_role_replaces_customer_and_admin_with_developer(
    monkeypatch: Any,
) -> None:
    user_id = uuid.uuid4()
    user = SimpleNamespace(
        id=user_id,
        email="staff@example.test",
    )
    customer = assignment(user_id, RoleName.customer)
    administrator = assignment(
        user_id,
        RoleName.administrator,
    )
    database = RoleDatabase(
        user=user,
        assignments=[customer, administrator],
    )
    audit_events: list[dict[str, object]] = []

    monkeypatch.setattr(
        manage_user_role,
        "SessionLocal",
        lambda: database,
    )
    monkeypatch.setattr(
        manage_user_role,
        "record_audit_event",
        lambda db, **kwargs: audit_events.append(kwargs),
    )

    result = manage_user_role.set_staff_role(
        email="STAFF@example.test",
        role=RoleName.developer,
        confirm_replace_all_roles=True,
    )

    assert result == 0
    assert database.deleted == [customer, administrator]

    added_roles = {
        item.role
        for item in database.added
        if isinstance(item, UserRole)
    }
    assert added_roles == {RoleName.developer}
    assert database.committed is True

    metadata = audit_events[0]["metadata"]
    assert metadata == {
        "previous_roles": [
            "administrator",
            "customer",
        ],
        "new_roles": ["developer"],
        "source": "local_role_cli",
        "mode": "replace_all_roles",
    }


def test_set_staff_role_requires_explicit_confirmation(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        manage_user_role,
        "SessionLocal",
        lambda: (_ for _ in ()).throw(
            AssertionError("database should not be opened")
        ),
    )

    result = manage_user_role.set_staff_role(
        email="staff@example.test",
        role=RoleName.employee,
        confirm_replace_all_roles=False,
    )

    assert result == 2


def test_set_staff_role_rejects_legacy_manager(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        manage_user_role,
        "SessionLocal",
        lambda: (_ for _ in ()).throw(
            AssertionError("database should not be opened")
        ),
    )

    result = manage_user_role.set_staff_role(
        email="staff@example.test",
        role=RoleName.manager,
        confirm_replace_all_roles=True,
    )

    assert result == 2


def test_set_staff_role_protects_final_active_developer(
    monkeypatch: Any,
) -> None:
    user_id = uuid.uuid4()
    user = SimpleNamespace(
        id=user_id,
        email="developer@example.test",
    )
    developer = assignment(
        user_id,
        RoleName.developer,
    )
    database = RoleDatabase(
        user=user,
        assignments=[developer],
        other_active_developers=0,
    )

    monkeypatch.setattr(
        manage_user_role,
        "SessionLocal",
        lambda: database,
    )

    result = manage_user_role.set_staff_role(
        email="developer@example.test",
        role=RoleName.administrator,
        confirm_replace_all_roles=True,
    )

    assert result == 2
    assert database.deleted == []
    assert database.added == []
    assert database.committed is False


def test_set_staff_role_is_noop_when_exact_role_already_present(
    monkeypatch: Any,
) -> None:
    user_id = uuid.uuid4()
    user = SimpleNamespace(
        id=user_id,
        email="employee@example.test",
    )
    employee = assignment(
        user_id,
        RoleName.employee,
    )
    database = RoleDatabase(
        user=user,
        assignments=[employee],
    )

    monkeypatch.setattr(
        manage_user_role,
        "SessionLocal",
        lambda: database,
    )

    result = manage_user_role.set_staff_role(
        email="employee@example.test",
        role=RoleName.employee,
        confirm_replace_all_roles=True,
    )

    assert result == 0
    assert database.deleted == []
    assert database.added == []
    assert database.committed is False
