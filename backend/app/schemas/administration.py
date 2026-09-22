from pydantic import BaseModel, Field, field_validator

from app.models.identity import RoleName

WEB_MANAGED_OPERATIONS_ROLES = frozenset(
    {
        RoleName.employee,
        RoleName.manager,
        RoleName.administrator,
    }
)


class AdministrationAccountRead(BaseModel):
    id: str
    email: str
    status: str
    roles: list[str] = Field(
        default_factory=list,
    )
    email_verified: bool
    mfa_required: bool
    mfa_enrolled: bool
    created_at: str
    last_login_at: str | None


class AdministrationRolesUpdate(BaseModel):
    roles: list[RoleName] = Field(
        default_factory=list,
    )

    @field_validator("roles")
    @classmethod
    def validate_roles(
        cls,
        value: list[RoleName],
    ) -> list[RoleName]:
        unique_roles = set(value)

        invalid = (
            unique_roles
            - WEB_MANAGED_OPERATIONS_ROLES
        )

        if invalid:
            names = ", ".join(
                sorted(
                    role.value
                    for role in invalid
                )
            )

            raise ValueError(
                "Only employee, manager, and "
                "administrator roles are "
                "managed in the web console. "
                f"Invalid role(s): {names}."
            )

        return sorted(
            unique_roles,
            key=lambda role: role.value,
        )
