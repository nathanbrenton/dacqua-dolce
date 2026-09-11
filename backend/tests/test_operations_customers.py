import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from app.api import operations
from app.models.customer import (
    CustomerProfile,
)
from app.models.identity import (
    RoleName,
    UserStatus,
)


class ScalarResult:
    def __init__(
        self,
        values: list[object],
    ) -> None:
        self.values = values

    def all(self) -> list[object]:
        return self.values


class RosterDatabase:
    def __init__(
        self,
        *,
        customer: SimpleNamespace,
        profile: SimpleNamespace | None,
        address: SimpleNamespace,
    ) -> None:
        self.customer = customer
        self.profile = profile
        self.address = address
        self.scalar_calls = 0
        self.customer_query = ""

    def scalars(
        self,
        statement: object,
    ) -> ScalarResult:
        self.scalar_calls += 1

        if self.scalar_calls == 1:
            self.customer_query = str(statement)

            return ScalarResult(
                [self.customer]
            )

        return ScalarResult(
            [self.address]
        )

    def get(
        self,
        model: object,
        identifier: object,
    ) -> SimpleNamespace | None:
        assert model is CustomerProfile
        assert identifier == self.customer.id

        return self.profile


def test_operations_customer_roster_uses_customer_role(
    monkeypatch: Any,
) -> None:
    customer_id = uuid.uuid4()

    customer = SimpleNamespace(
        id=customer_id,
        email="customer@example.com",
        status=UserStatus.active,
        created_at=datetime.now(UTC),
    )

    profile = SimpleNamespace(
        first_name="Dory",
        last_name="Tang",
        phone="+19495551234",
    )

    address = SimpleNamespace(
        id=uuid.uuid4(),
        label="Home",
        line1="123 Test Street",
        line2=None,
        city="Costa Mesa",
        region_code="CA",
        postal_code="92626",
        country_code="US",
        is_default_shipping=True,
        is_default_billing=True,
    )

    database = RosterDatabase(
        customer=customer,
        profile=profile,
        address=address,
    )

    access_checked = False

    def allow_operations(
        db: object,
        *,
        user: object,
    ) -> set[RoleName]:
        nonlocal access_checked
        access_checked = True

        return {RoleName.employee}

    monkeypatch.setattr(
        operations,
        "require_operations",
        allow_operations,
    )

    result = operations.list_customers(
        database,  # type: ignore[arg-type]
        SimpleNamespace(
            id=uuid.uuid4(),
        ),  # type: ignore[arg-type]
    )

    assert access_checked is True
    assert len(result) == 1

    roster_customer = result[0]

    assert roster_customer.id == str(customer_id)
    assert roster_customer.email == (
        "customer@example.com"
    )
    assert roster_customer.first_name == "Dory"
    assert roster_customer.last_name == "Tang"
    assert roster_customer.phone == (
        "+19495551234"
    )
    assert len(roster_customer.addresses) == 1

    roster_address = (
        roster_customer.addresses[0]
    )

    assert roster_address.city == (
        "Costa Mesa"
    )
    assert (
        roster_address.is_default_shipping
        is True
    )

    assert "user_roles" in (
        database.customer_query
    )
    assert "role" in (
        database.customer_query
    )


def test_operations_customer_without_profile_is_supported() -> None:
    customer = SimpleNamespace(
        id=uuid.uuid4(),
        email="minimal@example.com",
        status=UserStatus.active,
        created_at=datetime.now(UTC),
    )

    address = SimpleNamespace(
        id=uuid.uuid4(),
        label="Home",
        line1="456 Test Avenue",
        line2=None,
        city="Irvine",
        region_code="CA",
        postal_code="92618",
        country_code="US",
        is_default_shipping=False,
        is_default_billing=False,
    )

    database = RosterDatabase(
        customer=customer,
        profile=None,
        address=address,
    )

    # Skip the roster-query slot because this test
    # calls the response helper directly.
    database.scalar_calls = 1

    result = operations.operations_customer_read(
        database,  # type: ignore[arg-type]
        user=customer,  # type: ignore[arg-type]
    )

    assert result.first_name is None
    assert result.last_name is None
    assert result.phone is None
