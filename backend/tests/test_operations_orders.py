import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api import operations
from app.models.commerce import OrderStatus
from app.models.customer import CustomerProfile
from app.models.identity import RoleName, User


class ScalarResult:
    def __init__(
        self,
        values: list[object],
    ) -> None:
        self.values = values

    def all(self) -> list[object]:
        return self.values


class OrderHistoryDatabase:
    def __init__(
        self,
        *,
        roles: list[RoleName],
        order: SimpleNamespace | None = None,
        item: SimpleNamespace | None = None,
        customer: SimpleNamespace | None = None,
        profile: SimpleNamespace | None = None,
    ) -> None:
        self.roles = roles
        self.order = order
        self.item = item
        self.customer = customer
        self.profile = profile
        self.statements: list[str] = []

    def scalars(
        self,
        statement: object,
    ) -> ScalarResult:
        query = str(statement)
        self.statements.append(query)

        if query.startswith("SELECT user_roles.role"):
            return ScalarResult(self.roles)

        if "FROM orders" in query:
            return ScalarResult(
                [] if self.order is None else [self.order]
            )

        if "FROM order_items" in query:
            return ScalarResult(
                [] if self.item is None else [self.item]
            )

        raise AssertionError(
            f"Unexpected query: {query}"
        )

    def get(
        self,
        model: object,
        identifier: object,
    ) -> SimpleNamespace | None:
        if model is User:
            assert self.customer is not None
            assert identifier == self.customer.id
            return self.customer

        if model is CustomerProfile:
            assert self.customer is not None
            assert identifier == self.customer.id
            return self.profile

        raise AssertionError(
            f"Unexpected model lookup: {model}"
        )


def test_customer_cannot_access_operations_order_history() -> None:
    database = OrderHistoryDatabase(
        roles=[RoleName.customer],
    )

    with pytest.raises(HTTPException) as exc:
        operations.list_orders(
            database,  # type: ignore[arg-type]
            SimpleNamespace(
                id=uuid.uuid4(),
            ),  # type: ignore[arg-type]
        )

    assert exc.value.status_code == 403


def test_operations_order_history_is_customer_linked_and_bounded() -> None:
    customer_id = uuid.uuid4()
    order_id = uuid.uuid4()

    customer = SimpleNamespace(
        id=customer_id,
        email="customer@example.com",
    )
    profile = SimpleNamespace(
        first_name="Dory",
        last_name="Tang",
        phone="+19495551234",
    )
    order = SimpleNamespace(
        id=order_id,
        user_id=customer_id,
        status=OrderStatus.paid,
        total_amount_minor=249900,
        currency="USD",
        created_at=datetime.now(UTC),
    )
    item = SimpleNamespace(
        id=uuid.uuid4(),
        sku_snapshot="DD5RO",
        name_snapshot="Origin",
        quantity=1,
        unit_amount_minor=249900,
        line_total_minor=249900,
        currency="USD",
        created_at=datetime.now(UTC),
    )

    database = OrderHistoryDatabase(
        roles=[RoleName.employee],
        order=order,
        item=item,
        customer=customer,
        profile=profile,
    )

    result = operations.list_orders(
        database,  # type: ignore[arg-type]
        SimpleNamespace(
            id=uuid.uuid4(),
        ),  # type: ignore[arg-type]
    )

    assert len(result) == 1

    payload = result[0].model_dump()

    assert payload == {
        "id": str(order_id),
        "status": "paid",
        "total_amount_minor": 249900,
        "currency": "USD",
        "created_at": order.created_at.isoformat(),
        "customer": {
            "id": str(customer_id),
            "email": "customer@example.com",
            "first_name": "Dory",
            "last_name": "Tang",
            "phone": "+19495551234",
        },
        "items": [
            {
                "sku": "DD5RO",
                "name": "Origin",
                "quantity": 1,
                "unit_amount_minor": 249900,
                "line_total_minor": 249900,
                "currency": "USD",
            }
        ],
    }

    combined_queries = "\n".join(
        database.statements
    )

    assert "user_roles" in combined_queries
    assert "orders" in combined_queries
    assert "order_items" in combined_queries
    assert "payment_provider_references" not in (
        combined_queries
    )

    assert "provider_payment_id" not in payload
    assert "provider_checkout_id" not in payload
    assert "payment_method_last4" not in payload
