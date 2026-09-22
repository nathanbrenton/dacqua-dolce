import pytest
from pydantic import ValidationError

from app.models.identity import RoleName
from app.schemas.administration import (
    AdministrationRolesUpdate,
)


def test_web_role_update_accepts_operations_roles() -> None:
    payload = AdministrationRolesUpdate(
        roles=[
            RoleName.employee,
            RoleName.administrator,
            RoleName.employee,
        ]
    )

    assert payload.roles == [
        RoleName.administrator,
        RoleName.employee,
    ]


@pytest.mark.parametrize(
    "role",
    [
        RoleName.customer,
        RoleName.developer,
    ],
)
def test_web_role_update_rejects_non_web_managed_roles(
    role: RoleName,
) -> None:
    with pytest.raises(
        ValidationError,
    ):
        AdministrationRolesUpdate(
            roles=[role],
        )
