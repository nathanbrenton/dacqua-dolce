# PT30 — Geographic Sales-Area Infrastructure

## Purpose

PT30 adds one centralized, explicit sales-area policy for commercial delivery
addresses. It deliberately does not reinterpret the client’s phrase
“Continental United States.”

Customer address-book storage remains unrestricted. A saved address may exist
outside the active sales area. Commercial use of that address is what becomes
restricted when enforcement is enabled.

## Enforcement points

The same backend policy is checked when:

1. Operations presents a formal quote.
2. An approved formal quote is materialized into an order.
3. A hosted payment checkout is started.

The repeated checks are intentional defense in depth. The customer Account UI
also displays delivery eligibility and disables quote approval for an
out-of-area delivery address when enforcement is enabled.

## Configuration

PT30 is disabled by default so deployment does not silently choose a geographic
interpretation or unexpectedly block existing production workflows.

Environment variables:

- `DACQUA_SALES_AREA_MODE`
  - `disabled` (default)
  - `allowlist`
- `DACQUA_SALES_AREA_COUNTRY_CODE`
  - defaults to `US`
- `DACQUA_SALES_AREA_REGION_CODES`
  - comma-separated two-letter region codes
  - required when mode is `allowlist`
- `DACQUA_SALES_AREA_LABEL`
  - customer-facing label for the configured area
  - defaults to `D’Acqua Dolce’s configured sales area`

Example only — not an approved production configuration:

```text
DACQUA_SALES_AREA_MODE=allowlist
DACQUA_SALES_AREA_COUNTRY_CODE=US
DACQUA_SALES_AREA_REGION_CODES=CA,OR,WA
DACQUA_SALES_AREA_LABEL=Launch delivery area
```

The example is for configuration mechanics only. It is not a business decision.

## Production commissioning gate

Do not enable `allowlist` in production until the business owner explicitly
approves the exact included region-code set. In particular, PT30 does not decide
whether the phrase “Continental United States” includes or excludes Alaska,
Washington D.C., or United States territories.

## Deferred

PT30 does not add:

- tax-engine automation;
- carrier-rate calculation;
- international sales;
- address verification/geocoding;
- automatic legal interpretation of state/territory terms;
- payment-provider commissioning.

No database migration is required for PT30.
