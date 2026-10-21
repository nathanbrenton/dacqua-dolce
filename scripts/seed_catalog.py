"""Retired historical SKU seeder.

This entry point is intentionally disabled: it contains obsolete product SKUs.
Use the canonical PT41 catalog rollout instead. No database writes occur here.
"""

raise SystemExit(
    "Legacy seed_catalog.py disabled to prevent obsolete SKU restoration. "
    "Use: cd backend && python3 -m app.cli.pt41_catalog_rollout plan "
    "(then apply only after reviewing outstanding commitments)."
)
