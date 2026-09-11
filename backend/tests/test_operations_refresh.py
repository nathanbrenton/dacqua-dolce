import uuid
from typing import Any

from app.api.operations import (
    load_product_for_operations,
)


class CapturingDatabase:
    def __init__(self) -> None:
        self.populate_existing = False

    def scalar(
        self,
        statement: Any,
    ) -> None:
        options = statement.get_execution_options()

        self.populate_existing = bool(options.get("populate_existing"))

        return None


def test_operations_reload_refreshes_identity_map() -> None:
    database = CapturingDatabase()

    load_product_for_operations(
        database,  # type: ignore[arg-type]
        uuid.uuid4(),
    )

    assert database.populate_existing is True
