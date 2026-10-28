"""PT54-C3: offline proposal intake, NEVER an approval/fitment/price authority.

This deliberately cannot write to the catalog, formal quote service, or the
pending-only Pureline registry. Supplier data remains advisory until a separate
reviewed commercial release expressly enables the affected options.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from app.schemas.product_configuration import CARTRIDGE_CHOICES, FITTING_CHOICES, SKU_FAMILY

SCHEMA_VERSION = 1
PURPOSE = "external_evidence_intake_only"
KINDS = ("fitting", "pureline_cartridge", "harmony_2cf")
VALVES = ("clack", "performance")
HARMONY_CONFIGURATIONS = ("pass_through_only", "solo", "duo", "trio")
CLAIMS = ("not_reviewed", "supplier_claims_compatible", "supplier_claims_incompatible")
SOURCES = (
    "manufacturer_document",
    "supplier_document",
    "supplier_quotation",
    "manufacturer_correspondence",
    "other",
)
CLAIM_FIELDS = frozenset({
    "manufacturer", "manufacturer_model", "supplier_part_number", "compatibility_claim",
    "claimed_housing_models", "claimed_positions", "proposed_sku",
    "supplier_cost_usd", "proposed_selling_price_usd",
})
EVIDENCE_FIELDS = frozenset({"source_type", "source_reference", "source_date", "notes"})
RECORD_FIELDS = frozenset({"kind", "identity", "claim", "evidence"})
TOP_FIELDS = frozenset({"schema_version", "purpose", "records"})
CLAIM_TEMPLATE = {
    "manufacturer": None, "manufacturer_model": None, "supplier_part_number": None,
    "compatibility_claim": "not_reviewed", "claimed_housing_models": [],
    "claimed_positions": [], "proposed_sku": None, "supplier_cost_usd": None,
    "proposed_selling_price_usd": None,
}
EVIDENCE_TEMPLATE = {
    "source_type": None,
    "source_reference": None,
    "source_date": None,
    "notes": None,
}
_MONEY = re.compile(r"(?:0|[1-9][0-9]{0,8})(?:\.[0-9]{1,2})?\Z")
_SKU = re.compile(r"[A-Z0-9][A-Z0-9_-]{1,31}\Z")
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")


def expected_identities() -> list[tuple[str, tuple[str, ...]]]:
    """The 20 + 14 + 4 exact review targets from current application definitions."""
    return (
        [("fitting", (valve, order_no))
         for valve in VALVES for order_no in sorted(FITTING_CHOICES)]
        + [("pureline_cartridge", (category, name))
           for category in sorted(CARTRIDGE_CHOICES)
           for name in sorted(CARTRIDGE_CHOICES[category])]
        + [("harmony_2cf", (configuration,))
           for configuration in HARMONY_CONFIGURATIONS]
    )


def identity_fields(kind: str, key: tuple[str, ...]) -> dict[str, str]:
    if kind == "fitting":
        return {"valve": key[0], "reference_order_no": key[1]}
    if kind == "pureline_cartridge":
        return {"category": key[0], "requested_description": key[1]}
    if kind == "harmony_2cf":
        return {"configuration": key[0]}
    raise ValueError("Unknown commercial evidence kind")


def make_template() -> dict[str, Any]:
    """Return an editable intake form with zero claims, models, SKUs or prices."""
    return {
        "schema_version": SCHEMA_VERSION, "purpose": PURPOSE,
        "records": [
            {"kind": kind, "identity": identity_fields(kind, key),
             "claim": {**CLAIM_TEMPLATE, "claimed_housing_models": [], "claimed_positions": []},
             "evidence": EVIDENCE_TEMPLATE.copy()}
            for kind, key in expected_identities()
        ],
    }


def _optional_text(value: Any, name: str, *, limit: int = 160) -> None:
    if value is None:
        return
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{name} must be a nonempty string of at most {limit} characters")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise ValueError(f"{name} contains control characters")


def _money(value: Any, name: str) -> None:
    if value is None:
        return
    if not isinstance(value, str) or not _MONEY.fullmatch(value):
        raise ValueError(
            f"{name} must be a nonnegative USD decimal string with at most two decimals"
        )
    try:
        if not Decimal(value).is_finite():
            raise ValueError(f"{name} must be finite")
    except InvalidOperation as exc:
        raise ValueError(f"{name} invalid decimal") from exc


def _identity_key(kind: Any, identity: Any) -> tuple[str, tuple[str, ...]]:
    if kind not in KINDS or not isinstance(identity, dict):
        raise ValueError("Unknown kind or malformed identity")
    if kind == "fitting":
        fields = ("valve", "reference_order_no")
    elif kind == "pureline_cartridge":
        fields = ("category", "requested_description")
    else:
        fields = ("configuration",)
    if set(identity) != set(fields) or any(not isinstance(identity[f], str) for f in fields):
        raise ValueError("Unexpected identity fields")
    return kind, tuple(identity[f] for f in fields)


def validate_intake(payload: Any) -> list[dict[str, Any]]:
    """Validate shape, identities, proposal types and source metadata.

    Missing evidence does not become an approval; the review report flags it.
    """
    if (not isinstance(payload, dict) or set(payload) != TOP_FIELDS
            or type(payload["schema_version"]) is not int
            or payload["schema_version"] != SCHEMA_VERSION or payload["purpose"] != PURPOSE
            or not isinstance(payload["records"], list)):
        raise ValueError("Invalid or unauthorized evidence intake structure")
    expected = set(expected_identities())
    seen: set[tuple[str, tuple[str, ...]]] = set()
    validated = []
    proposed_skus: set[str] = set()
    for record in payload["records"]:
        if not isinstance(record, dict) or set(record) != RECORD_FIELDS:
            raise ValueError("Unexpected record fields; approvals are forbidden in evidence intake")
        kind, key = _identity_key(record["kind"], record["identity"])
        if (kind, key) not in expected or (kind, key) in seen:
            raise ValueError("Unknown or duplicate reference identity")
        seen.add((kind, key))
        claim, evidence = record["claim"], record["evidence"]
        if (not isinstance(claim, dict) or set(claim) != CLAIM_FIELDS
                or not isinstance(evidence, dict) or set(evidence) != EVIDENCE_FIELDS):
            raise ValueError("Unexpected claim/evidence fields; authorization is not accepted")
        for field in ("manufacturer", "manufacturer_model", "supplier_part_number"):
            _optional_text(claim[field], field)
        for field in ("source_reference", "notes"):
            _optional_text(evidence[field], field, limit=500 if field == "notes" else 250)
        if claim["compatibility_claim"] not in CLAIMS:
            raise ValueError("Compatibility is a supplier claim, never an approval")
        if (
            not isinstance(claim["claimed_housing_models"], list)
            or not isinstance(claim["claimed_positions"], list)
        ):
            raise ValueError("Invalid proposed compatibility arrays")
        models = claim["claimed_housing_models"]
        if len(models) > 12 or len(set(map(str, models))) != len(models):
            raise ValueError("Duplicate or excessive claimed housing models")
        for model in models:
            _optional_text(model, "claimed_housing_model")
            if not isinstance(model, str):
                raise ValueError("Invalid claimed housing model")
        positions = claim["claimed_positions"]
        if (
            any(type(n) is not int or n not in (1, 2, 3) for n in positions)
            or len(set(positions)) != len(positions)
        ):
            raise ValueError("Invalid proposed Pureline positions")
        _money(claim["supplier_cost_usd"], "supplier_cost_usd")
        _money(claim["proposed_selling_price_usd"], "proposed_selling_price_usd")
        sku = claim["proposed_sku"]
        if sku is not None:
            if (kind != "harmony_2cf" or not isinstance(sku, str)
                    or not _SKU.fullmatch(sku) or sku in SKU_FAMILY or sku in proposed_skus):
                raise ValueError(
                    "Proposed SKU must be a unique, previously unused Harmony 2.0 identity"
                )
            proposed_skus.add(sku)
        if kind != "pureline_cartridge" and (models or positions):
            raise ValueError("Housing fitment proposals apply only to cartridge records")
        if kind == "harmony_2cf" and claim["compatibility_claim"] != "not_reviewed":
            raise ValueError(
                "Harmony catalog readiness is not a supplier fitting compatibility claim"
            )
        if kind != "harmony_2cf" and sku is not None:
            raise ValueError("SKU proposals are limited to Harmony 2.0 entries")
        if evidence["source_type"] is not None and evidence["source_type"] not in SOURCES:
            raise ValueError("Unknown evidence source type")
        source_date = evidence["source_date"]
        if source_date is not None:
            if not isinstance(source_date, str) or not _DATE.fullmatch(source_date):
                raise ValueError("Invalid evidence source date")
            try:
                date.fromisoformat(source_date)
            except ValueError as exc:
                raise ValueError("Invalid calendar date in evidence") from exc
        proposed_fields = [
            field for field in CLAIM_FIELDS if claim[field] not in (None, [], "not_reviewed")
        ]
        blockers = []
        if not proposed_fields:
            blockers.append("No supplier/manufacturer claims received")
        if not evidence["source_type"] or not evidence["source_reference"] or not source_date:
            blockers.append("Traceable evidence source, reference, and date required")
        if kind == "harmony_2cf" and (sku is None or claim["proposed_selling_price_usd"] is None):
            blockers.append("Harmony 2.0 SKU and proposed selling price still required")
        if kind == "pureline_cartridge" and (not claim["manufacturer_model"] or not models):
            blockers.append("Identified manufacturer model and housing evidence required")
        if kind == "fitting" and claim["compatibility_claim"] == "not_reviewed":
            blockers.append("Valve-specific fitment claim not supplied")
        validated.append({
            "kind": kind, "identity": record["identity"],
            "supplied_claim_fields": sorted(proposed_fields),
            "source_provided": bool(
                evidence["source_type"] and evidence["source_reference"] and source_date
            ),
            "blockers": blockers,
            "review_state": "incomplete" if blockers else "submitted_for_staff_review",
            "commercially_authorized": False,
        })
    if seen != expected:
        raise ValueError("Evidence intake is incomplete: expected exactly 38 known references")
    return validated


def review_report(payload: Any) -> dict[str, Any]:
    records = validate_intake(payload)
    counts = Counter(record["kind"] for record in records)
    return {
        "schema_version": 1,
        "scope": "NON_AUTHORIZING_STAFF_REVIEW_REPORT",
        "total_reference_records": len(records),
        "fitting_valve_pairs": counts["fitting"],
        "pureline_descriptions": counts["pureline_cartridge"],
        "harmony_2cf_configurations": counts["harmony_2cf"],
        "submitted_for_staff_review": sum(
            r["review_state"] == "submitted_for_staff_review" for r in records
        ),
        "commercially_authorized": 0,
        "records": records,
    }


def load_intake(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as source:
        payload = json.load(source)
    validate_intake(payload)
    return payload


def as_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"
