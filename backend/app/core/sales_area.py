from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal


class SalesAreaConfigurationError(ValueError):
    pass


class SalesAreaEligibilityError(ValueError):
    pass


@dataclass(frozen=True)
class SalesAreaPolicy:
    mode: Literal["disabled", "allowlist"]
    country_code: str
    region_codes: frozenset[str]
    label: str

    @property
    def enforcement_enabled(self) -> bool:
        return self.mode == "allowlist"


@dataclass(frozen=True)
class SalesAreaDecision:
    eligible: bool
    message: str | None


def _normalize_code(value: str, *, field_name: str) -> str:
    normalized = value.strip().upper()
    if len(normalized) != 2 or not normalized.isalpha():
        raise SalesAreaConfigurationError(
            f"{field_name} must be a two-letter code."
        )
    return normalized


def load_sales_area_policy(
    environ: Mapping[str, str] | None = None,
) -> SalesAreaPolicy:
    values = os.environ if environ is None else environ

    mode = values.get(
        "DACQUA_SALES_AREA_MODE",
        "disabled",
    ).strip().lower()
    if mode not in {"disabled", "allowlist"}:
        raise SalesAreaConfigurationError(
            "DACQUA_SALES_AREA_MODE must be 'disabled' or 'allowlist'."
        )

    country_code = _normalize_code(
        values.get(
            "DACQUA_SALES_AREA_COUNTRY_CODE",
            "US",
        ),
        field_name="DACQUA_SALES_AREA_COUNTRY_CODE",
    )

    raw_regions = values.get(
        "DACQUA_SALES_AREA_REGION_CODES",
        "",
    )
    region_codes = frozenset(
        _normalize_code(
            value,
            field_name="DACQUA_SALES_AREA_REGION_CODES",
        )
        for value in raw_regions.split(",")
        if value.strip()
    )

    label = values.get(
        "DACQUA_SALES_AREA_LABEL",
        "D’Acqua Dolce’s configured sales area",
    ).strip()
    if not label:
        raise SalesAreaConfigurationError(
            "DACQUA_SALES_AREA_LABEL must not be blank."
        )

    if mode == "allowlist" and not region_codes:
        raise SalesAreaConfigurationError(
            "DACQUA_SALES_AREA_REGION_CODES must contain at least one "
            "two-letter region code when sales-area enforcement is enabled."
        )

    return SalesAreaPolicy(
        mode=mode,
        country_code=country_code,
        region_codes=region_codes,
        label=label,
    )


@lru_cache
def get_sales_area_policy() -> SalesAreaPolicy:
    return load_sales_area_policy()


def evaluate_delivery_address(
    address: Mapping[str, object] | None,
    *,
    policy: SalesAreaPolicy | None = None,
) -> SalesAreaDecision:
    effective_policy = policy or get_sales_area_policy()

    if not effective_policy.enforcement_enabled:
        return SalesAreaDecision(
            eligible=True,
            message=None,
        )

    if address is None:
        return SalesAreaDecision(
            eligible=False,
            message=(
                "A delivery address is required before sales-area "
                "eligibility can be confirmed."
            ),
        )

    country_code = str(
        address.get("country_code") or ""
    ).strip().upper()
    region_code = str(
        address.get("region_code") or ""
    ).strip().upper()

    if (
        country_code != effective_policy.country_code
        or region_code not in effective_policy.region_codes
    ):
        return SalesAreaDecision(
            eligible=False,
            message=(
                "This delivery address is outside "
                f"{effective_policy.label}."
            ),
        )

    return SalesAreaDecision(
        eligible=True,
        message=(
            "This delivery address is within "
            f"{effective_policy.label}."
        ),
    )


def require_delivery_address_in_sales_area(
    address: Mapping[str, object] | None,
    *,
    policy: SalesAreaPolicy | None = None,
) -> SalesAreaDecision:
    decision = evaluate_delivery_address(
        address,
        policy=policy,
    )
    if not decision.eligible:
        raise SalesAreaEligibilityError(
            decision.message
            or "This delivery address is outside the configured sales area."
        )
    return decision
