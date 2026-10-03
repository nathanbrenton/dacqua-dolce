# PT30 — Geographic Sales-Area Infrastructure

## Purpose

PT30 added one centralized, explicit sales-area policy for commercial delivery
addresses. At the time, it deliberately did not reinterpret the client’s phrase
“Continental United States.” PT35 later resolved that business decision as the
48 contiguous states plus Washington, DC and activated that set as the canonical
launch policy.

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

PT30 originally defaulted to disabled so deployment could not silently choose a
geographic interpretation. PT35 supersedes that temporary default: the approved
launch policy now defaults to `allowlist` for the 48 contiguous states plus
Washington, DC. Operators may still set an explicit override, but PT34/PT35
readiness reports any drift from the approved launch set as `Action required`.

Environment variables:

- `DACQUA_SALES_AREA_MODE`
  - `allowlist` (PT35 default)
  - `disabled` (explicit operator override)
- `DACQUA_SALES_AREA_COUNTRY_CODE`
  - defaults to `US`
- `DACQUA_SALES_AREA_REGION_CODES`
  - comma-separated two-letter region codes
  - defaults to the approved PT35 launch set
  - required when mode is `allowlist` if explicitly overridden
- `DACQUA_SALES_AREA_LABEL`
  - customer-facing label for the configured area
  - defaults to `the contiguous United States and Washington, DC`

Approved PT35 launch configuration:

```text
DACQUA_SALES_AREA_MODE=allowlist
DACQUA_SALES_AREA_COUNTRY_CODE=US
DACQUA_SALES_AREA_REGION_CODES=AL,AR,AZ,CA,CO,CT,DC,DE,FL,GA,IA,ID,IL,IN,KS,KY,LA,MA,MD,ME,MI,MN,MO,MS,MT,NC,ND,NE,NH,NJ,NM,NV,NY,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VA,VT,WA,WI,WV,WY
DACQUA_SALES_AREA_LABEL="the contiguous United States and Washington, DC"
```

## Production commissioning gate

The PT30 commissioning gate was resolved by PT35. The approved initial launch
area is exactly the 48 contiguous states plus Washington, DC. Alaska, Hawaii,
Puerto Rico, and other U.S. territories are excluded from the initial launch
area. Production runtime configuration should explicitly match the approved set
before PT35 is commissioned.

## Deferred

PT30 does not add:

- tax-engine automation;
- carrier-rate calculation;
- international sales;
- address verification/geocoding;
- automatic legal interpretation of state/territory terms;
- payment-provider commissioning.

No database migration is required for PT30.
