"""Deterministic product family merchandising sort, independent of catalog records."""
import json

DEFAULT_FAMILY_ORDER = ("Refine", "Essence", "Origin", "Harmony")


def family_name(product: object) -> str:
    return (getattr(product, "product_family", None) or getattr(product, "name", "")).strip()


def available_families(products: list[object]) -> list[str]:
    return sorted({family_name(p) for p in products if family_name(p)}, key=str.casefold)


def stored_order(raw: str | None) -> list[str]:
    if not raw:
        return list(DEFAULT_FAMILY_ORDER)
    values = json.loads(raw)
    if not isinstance(values, list) or any(not isinstance(x, str) for x in values):
        raise ValueError("Invalid saved family order")
    return values


def complete_order(available: list[str], saved: list[str]) -> list[str]:
    known = set(available)
    result = list(dict.fromkeys(x for x in saved if x in known))
    result.extend(x for x in available if x not in result)
    return result


def sort_products(products: list[object], saved: list[str]) -> list[object]:
    rank = {name: i for i, name in enumerate(saved)}
    return sorted(products, key=lambda p: (
        rank.get(family_name(p), len(rank)),
        family_name(p).casefold(),
        getattr(p, "name", "").casefold(),
        str(getattr(p, "id", "")),
    ))
