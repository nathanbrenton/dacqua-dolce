from app.models.identity import (
    RoleName,
)


def test_operations_roles_remain_distinct_from_customer() -> None:
    operations_roles = {
        RoleName.employee,
        RoleName.manager,
        RoleName.administrator,
        RoleName.developer,
    }

    assert RoleName.customer not in operations_roles


def test_developer_is_valid_operations_role() -> None:
    assert RoleName.developer.value == "developer"
