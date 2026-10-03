from __future__ import annotations

from typing import Any

from sqlalchemy.sql import Select

from app.api import operations


class _EmptyScalarResult:
    def all(self) -> list[Any]:
        return []


class _CompilingDatabase:
    def scalars(self, statement: Select[Any]) -> _EmptyScalarResult:
        statement.compile()
        return _EmptyScalarResult()


def test_operations_quote_list_eager_load_paths_compile(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        operations,
        "require_operations",
        lambda db, user: None,
    )

    result = operations.list_quotes(
        _CompilingDatabase(),  # type: ignore[arg-type]
        object(),  # type: ignore[arg-type]
    )

    assert result == []
