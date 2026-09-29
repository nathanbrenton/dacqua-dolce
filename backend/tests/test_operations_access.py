from app.models.identity import RoleName
from app.services.operations_access import (
    ADMINISTRATION_ROLES,
    AUDIT_LOG_READ_ROLES,
    CUSTOMER_EQUIPMENT_WRITE_ROLES,
    OPERATIONS_ROLES,
    PRICING_INVENTORY_WRITE_ROLES,
)


def test_customer_role_is_not_operations() -> None:
    assert RoleName.customer not in OPERATIONS_ROLES


def test_employee_has_operations_and_read_only_pricing_access() -> None:
    assert RoleName.employee in OPERATIONS_ROLES
    assert RoleName.employee not in PRICING_INVENTORY_WRITE_ROLES


def test_administrator_can_write_pricing_but_cannot_read_audit_log() -> None:
    assert RoleName.administrator in PRICING_INVENTORY_WRITE_ROLES
    assert RoleName.administrator not in AUDIT_LOG_READ_ROLES


def test_developer_is_only_audit_log_reader() -> None:
    assert AUDIT_LOG_READ_ROLES == {RoleName.developer}


def test_customer_equipment_write_is_admin_or_developer_only() -> None:
    assert CUSTOMER_EQUIPMENT_WRITE_ROLES == {
        RoleName.administrator,
        RoleName.developer,
    }


def test_manager_is_legacy_operations_only() -> None:
    assert RoleName.manager in OPERATIONS_ROLES
    assert RoleName.manager not in PRICING_INVENTORY_WRITE_ROLES
    assert RoleName.manager not in ADMINISTRATION_ROLES
    assert RoleName.manager not in AUDIT_LOG_READ_ROLES


def test_administration_is_limited_to_admin_and_developer() -> None:
    assert ADMINISTRATION_ROLES == {
        RoleName.administrator,
        RoleName.developer,
    }
