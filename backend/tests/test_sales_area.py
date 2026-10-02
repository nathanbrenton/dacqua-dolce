import pytest

from app.core.sales_area import (
    SalesAreaConfigurationError,
    SalesAreaPolicy,
    evaluate_delivery_address,
    load_sales_area_policy,
    require_delivery_address_in_sales_area,
)


def address(
    *,
    region_code: str = "CA",
    country_code: str = "US",
) -> dict[str, object]:
    return {
        "recipient_name": "Customer",
        "line1": "123 Ocean Ave",
        "city": "Irvine",
        "region_code": region_code,
        "postal_code": "92618",
        "country_code": country_code,
    }


def test_disabled_sales_area_is_backward_compatible() -> None:
    policy = load_sales_area_policy({})

    assert policy.enforcement_enabled is False
    assert evaluate_delivery_address(
        address(region_code="ZZ", country_code="CA"),
        policy=policy,
    ).eligible


def test_allowlist_normalizes_and_allows_explicit_region() -> None:
    policy = load_sales_area_policy(
        {
            "DACQUA_SALES_AREA_MODE": "allowlist",
            "DACQUA_SALES_AREA_COUNTRY_CODE": "us",
            "DACQUA_SALES_AREA_REGION_CODES": "ca, OR,wa",
            "DACQUA_SALES_AREA_LABEL": "Launch delivery area",
        }
    )

    assert policy.region_codes == frozenset({"CA", "OR", "WA"})
    decision = evaluate_delivery_address(
        address(region_code="ca"),
        policy=policy,
    )
    assert decision.eligible
    assert decision.message == (
        "This delivery address is within Launch delivery area."
    )


@pytest.mark.parametrize(
    ("region_code", "country_code"),
    [
        ("NV", "US"),
        ("CA", "CA"),
    ],
)
def test_allowlist_rejects_out_of_area_destination(
    region_code: str,
    country_code: str,
) -> None:
    policy = SalesAreaPolicy(
        mode="allowlist",
        country_code="US",
        region_codes=frozenset({"CA", "OR", "WA"}),
        label="Launch delivery area",
    )

    with pytest.raises(
        ValueError,
        match="outside Launch delivery area",
    ):
        require_delivery_address_in_sales_area(
            address(
                region_code=region_code,
                country_code=country_code,
            ),
            policy=policy,
        )


def test_allowlist_requires_explicit_regions() -> None:
    with pytest.raises(
        SalesAreaConfigurationError,
        match="must contain at least one",
    ):
        load_sales_area_policy(
            {
                "DACQUA_SALES_AREA_MODE": "allowlist",
                "DACQUA_SALES_AREA_REGION_CODES": "",
            }
        )
