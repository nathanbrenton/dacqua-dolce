import pytest

from app.core.sales_area import (
    APPROVED_LAUNCH_COUNTRY_CODE,
    APPROVED_LAUNCH_REGION_CODES,
    APPROVED_LAUNCH_SALES_AREA_LABEL,
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


def test_default_sales_area_matches_approved_pt35_launch_policy() -> None:
    policy = load_sales_area_policy({})

    assert policy.enforcement_enabled is True
    assert policy.country_code == APPROVED_LAUNCH_COUNTRY_CODE
    assert policy.region_codes == APPROVED_LAUNCH_REGION_CODES
    assert policy.label == APPROVED_LAUNCH_SALES_AREA_LABEL
    assert len(policy.region_codes) == 49
    assert "DC" in policy.region_codes
    assert "AK" not in policy.region_codes
    assert "HI" not in policy.region_codes
    assert "PR" not in policy.region_codes


def test_disabled_sales_area_remains_an_explicit_operator_override() -> None:
    policy = load_sales_area_policy(
        {
            "DACQUA_SALES_AREA_MODE": "disabled",
            "DACQUA_SALES_AREA_REGION_CODES": "",
        }
    )

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
    "region_code",
    ["CA", "DC", "ME", "WY"],
)
def test_approved_launch_regions_are_eligible(region_code: str) -> None:
    policy = load_sales_area_policy({})

    decision = evaluate_delivery_address(
        address(region_code=region_code),
        policy=policy,
    )

    assert decision.eligible


@pytest.mark.parametrize(
    ("region_code", "country_code"),
    [
        ("AK", "US"),
        ("HI", "US"),
        ("PR", "US"),
        ("GU", "US"),
        ("VI", "US"),
        ("CA", "CA"),
    ],
)
def test_approved_launch_policy_rejects_out_of_area_destination(
    region_code: str,
    country_code: str,
) -> None:
    policy = load_sales_area_policy({})

    with pytest.raises(
        ValueError,
        match="outside the contiguous United States and Washington, DC",
    ):
        require_delivery_address_in_sales_area(
            address(
                region_code=region_code,
                country_code=country_code,
            ),
            policy=policy,
        )


@pytest.mark.parametrize(
    ("region_code", "country_code"),
    [
        ("NV", "US"),
        ("CA", "CA"),
    ],
)
def test_custom_allowlist_rejects_out_of_area_destination(
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


def test_allowlist_requires_explicit_regions_when_overridden_blank() -> None:
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
