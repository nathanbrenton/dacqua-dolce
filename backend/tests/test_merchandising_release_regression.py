"""Regression gates for merchandising defaults and deployment-safe preferences."""
from pathlib import Path
from types import SimpleNamespace
import importlib.util
import sqlite3

from app.api.catalog import catalog_card_visible_sku
from app.services.product_family_order import (
    DEFAULT_FAMILY_ORDER, available_families, complete_order, sort_products, stored_order
)


def _product(name):
    return SimpleNamespace(name=name, product_family=name, id=name)


def test_origin_remineralization_is_public_catalog_default():
    assert catalog_card_visible_sku("DD5ROAE") is True
    assert catalog_card_visible_sku("DD5RO") is False
    assert catalog_card_visible_sku("DD15CATRV") is True


def test_fallback_order_matches_staff_restore_default():
    assert DEFAULT_FAMILY_ORDER == ("Refine", "Essence", "Harmony", "Origin")
    panel = (Path(__file__).resolve().parents[2]
             / "frontend/src/components/operations/ProductFamilyOrderPanel.tsx").read_text()
    assert 'const defaults = ["Refine", "Essence", "Harmony", "Origin"];' in panel


def test_saved_custom_order_takes_precedence_over_changed_default():
    products = [_product(n) for n in ("Origin", "Refine", "Harmony", "Essence")]
    saved = '["Essence", "Refine", "Harmony", "Origin"]'
    order = complete_order(available_families(products), stored_order(saved))
    assert [p.name for p in sort_products(products, order)] == [
        "Essence", "Refine", "Harmony", "Origin"
    ]


def test_migration_preserves_custom_revision_two_and_updates_untouched_seed(monkeypatch):
    # Run the migration's actual SQL against isolated in-memory SQLite, not a live DB.
    root = Path(__file__).resolve().parents[1]
    path = root / "alembic/versions/d921ae0c7254_update_product_family_fallback_default.py"
    spec = importlib.util.spec_from_file_location("d921ae0c7254_regression", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE TABLE product_family_order (id INTEGER, revision INTEGER, families_json TEXT)")
        old = '["Refine", "Essence", "Origin", "Harmony"]'
        new = '["Refine", "Essence", "Harmony", "Origin"]'
        custom = '["Essence", "Refine", "Harmony", "Origin"]'
        for rev, initial, expected in ((1, old, new), (2, custom, custom), (1, custom, custom)):
            conn.execute("DELETE FROM product_family_order")
            conn.execute("INSERT INTO product_family_order VALUES (1, ?, ?)", (rev, initial))
            # op.execute receives a SQLAlchemy TextClause; SQLite runs the same SQL.
            monkeypatch.setattr(migration.op, "execute", lambda statement: conn.execute(str(statement)))
            migration.upgrade()
            observed = conn.execute("SELECT revision, families_json FROM product_family_order").fetchone()
            assert observed == (rev, expected)
    finally:
        conn.close()
