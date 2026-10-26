"""PT54-C2: complete, pending-only Pureline review register regression tests."""
from __future__ import annotations

import json

import pytest

from app.schemas.product_configuration import CARTRIDGE_CHOICES
from app.services.option_approval import review_pureline_cartridge
from app.services import pureline_commercial_review as commercial


def test_full_reference_catalog_remains_pending_only() -> None:
    records = commercial.load_pending_pureline_reviews()
    assert len(records) == 14
    assert set(records) == {(category, label) for category, labels in CARTRIDGE_CHOICES.items() for label in labels}
    assert all(item.approval_status == 'pending' and item.staff_review_required for item in records.values())
    assert all(item.manufacturer_model is None and item.supplier_cost_usd is None and item.authorized_unit_price_usd is None for item in records.values())
    assert all(not item.approved_positions and not item.compatible_housing_models for item in records.values())


@pytest.mark.parametrize('category,label', [(category, label) for category, labels in CARTRIDGE_CHOICES.items() for label in sorted(labels)])
@pytest.mark.parametrize('position', [1, 2, 3])
def test_every_choice_and_position_remains_unapproved(category: str, label: str, position: int) -> None:
    review = commercial.pending_cartridge_review(category, label, position=position)
    assert review.nominal_housing_length_inches == 20
    assert review.approval_status == 'pending'
    decision = review_pureline_cartridge(category, label)
    assert decision.staff_review_required
    assert decision.sales_price_authorized is False
    assert decision.compatibility_confirmed is False


@pytest.mark.parametrize('position', [0, 4, True, '1'])
def test_invalid_position_is_rejected(position: object) -> None:
    with pytest.raises(ValueError):
        commercial.pending_cartridge_review('iron', 'Iron cartridge', position=position)  # type: ignore[arg-type]


def test_unknown_cartridge_is_rejected() -> None:
    with pytest.raises(ValueError):
        commercial.pending_cartridge_review('carbon', 'not a listed product')


def test_registry_rejects_injected_price_or_approval(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    content = json.loads(commercial.REVIEW_FILE.read_text(encoding='utf-8'))
    for field, bad_value in [('authorized_unit_price_usd', '0.01'),
                             ('manufacturer_model', 'NOT-APPROVED'),
                             ('approval_status', 'approved'),
                             ('approved_positions', [1])]:
        modified = json.loads(json.dumps(content))
        modified['entries'][0][field] = bad_value
        path = tmp_path / 'reviews.json'
        path.write_text(json.dumps(modified))
        monkeypatch.setattr(commercial, 'REVIEW_FILE', path)
        commercial.load_pending_pureline_reviews.cache_clear()
        with pytest.raises(ValueError):
            commercial.load_pending_pureline_reviews()
    monkeypatch.setattr(commercial, 'REVIEW_FILE', tmp_path / 'missing.json')
    commercial.load_pending_pureline_reviews.cache_clear()
    with pytest.raises(FileNotFoundError):
        commercial.load_pending_pureline_reviews()
    commercial.load_pending_pureline_reviews.cache_clear()


def test_registry_rejects_missing_entries(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    content = json.loads(commercial.REVIEW_FILE.read_text(encoding='utf-8'))
    content['entries'].pop()
    path = tmp_path / 'incomplete.json'
    path.write_text(json.dumps(content))
    monkeypatch.setattr(commercial, 'REVIEW_FILE', path)
    commercial.load_pending_pureline_reviews.cache_clear()
    with pytest.raises(ValueError):
        commercial.load_pending_pureline_reviews()
    commercial.load_pending_pureline_reviews.cache_clear()
