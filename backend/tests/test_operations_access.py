from app.models.identity import RoleName
from app.services.operations_access import (
    OPERATIONS_ROLES,
    PRIVILEGED_OPERATIONS_ROLES,
)


def test_customer_role_is_not_operations() -> None:
    assert RoleName.customer not in OPERATIONS_ROLES


def test_employee_can_work_quote_and_inventory_queue() -> None:
    assert RoleName.employee in OPERATIONS_ROLES


def test_employee_cannot_change_pricing_policy() -> None:
    assert RoleName.employee not in PRIVILEGED_OPERATIONS_ROLES


def test_manager_can_change_pricing_policy() -> None:
    assert RoleName.manager in PRIVILEGED_OPERATIONS_ROLES
