import pytest
from pydantic import ValidationError

from app.schemas.operations import TaxClassificationUpdateRequest


def test_tax_classification_schema_trims_values() -> None:
    payload = TaxClassificationUpdateRequest(
        tax_code="  txcd_12345678  ",
        source_reference="  Stripe Tax code catalog review  ",
    )

    assert payload.tax_code == "txcd_12345678"
    assert payload.source_reference == "Stripe Tax code catalog review"


def test_tax_classification_schema_requires_exact_provider_code_shape() -> None:
    with pytest.raises(ValidationError, match="txcd_"):
        TaxClassificationUpdateRequest(
            tax_code="general tangible goods",
            source_reference="reviewed source",
        )


def test_tax_classification_schema_requires_source() -> None:
    with pytest.raises(ValidationError):
        TaxClassificationUpdateRequest(
            tax_code="txcd_12345678",
            source_reference=" ",
        )
