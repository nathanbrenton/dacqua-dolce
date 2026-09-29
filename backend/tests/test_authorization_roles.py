from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.dependencies.auth import (
    ADMINISTRATION_ROLES,
    AUDIT_LOG_READ_ROLES,
    OPERATIONS_ROLES,
    PRICING_INVENTORY_WRITE_ROLES,
    require_roles,
)
from app.models.identity import (
    RoleName,
    User,
    UserRole,
)


def build_user(
    *roles: RoleName,
) -> User:
    user = User(
        id=uuid4(),
        email="role-test@example.test",
    )

    user.roles = [
        UserRole(
            user_id=user.id,
            role=role,
        )
        for role in roles
    ]

    return user


def test_employee_can_access_operations() -> None:
    dependency = require_roles(*OPERATIONS_ROLES)

    assert dependency(build_user(RoleName.employee)).email == "role-test@example.test"


def test_employee_cannot_write_pricing_inventory() -> None:
    dependency = require_roles(*PRICING_INVENTORY_WRITE_ROLES)

    with pytest.raises(HTTPException) as exc:
        dependency(build_user(RoleName.employee))

    assert exc.value.status_code == 403


def test_manager_cannot_access_administration() -> None:
    dependency = require_roles(*ADMINISTRATION_ROLES)

    with pytest.raises(HTTPException) as exc:
        dependency(build_user(RoleName.manager))

    assert exc.value.status_code == 403


def test_developer_can_access_authorized_tiers() -> None:
    user = build_user(RoleName.developer)

    assert require_roles(*OPERATIONS_ROLES)(user) is user

    assert require_roles(*PRICING_INVENTORY_WRITE_ROLES)(user) is user

    assert require_roles(*ADMINISTRATION_ROLES)(user) is user
    assert require_roles(*AUDIT_LOG_READ_ROLES)(user) is user


def test_administrator_cannot_read_audit_log() -> None:
    dependency = require_roles(*AUDIT_LOG_READ_ROLES)
    with pytest.raises(HTTPException) as exc:
        dependency(build_user(RoleName.administrator))
    assert exc.value.status_code == 403
