# PT35 — Sales Geography Activation

## Purpose

PT35 resolves the geographic-launch decision that intentionally remained open
after PT30. D’Acqua Dolce’s initial commercial delivery area is exactly the 48
contiguous United States plus Washington, DC.

Excluded from the initial launch area:

- Alaska;
- Hawaii;
- Puerto Rico;
- Guam;
- U.S. Virgin Islands;
- Northern Mariana Islands;
- American Samoa;
- other non-approved domestic or international jurisdictions.

This milestone does not interpret tax nexus, carrier service, installation
coverage, or future expansion. It controls commercial delivery eligibility only.

## Canonical launch policy

Country: `US`

Approved region codes (49):

```text
AL,AR,AZ,CA,CO,CT,DC,DE,FL,GA,IA,ID,IL,IN,KS,KY,LA,MA,MD,ME,MI,MN,MO,MS,MT,NC,ND,NE,NH,NJ,NM,NV,NY,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VA,VT,WA,WI,WV,WY
```

The application now uses this approved policy as its sales-area default. The
environment variables remain available for controlled future changes or an
emergency operator override.

## Enforcement behavior

PT35 retains the PT30 defense-in-depth enforcement points. The same backend
policy is checked when:

1. Operations presents a formal quote;
2. an approved formal quote is converted into an order;
3. hosted payment checkout begins.

Customer address-book storage remains unrestricted. An address outside the
launch area may be stored, but it cannot pass the commercial delivery gate while
the approved allowlist is active.

The public sales-area API continues to expose the active policy so customer and
Operations UI behavior can reflect the same backend-authoritative decision.

## Launch-readiness behavior

The PT34 Sales area check is stricter under PT35. It reports `Ready` only when:

- enforcement mode is `allowlist`;
- country is `US`; and
- the configured region set exactly equals the approved 49-code set.

A missing approved region, an unexpected region, the wrong country, disabled
enforcement, or invalid configuration reports `Action required`. Evidence shows
the detected drift without silently altering configuration.

## Runtime configuration

Recommended production runtime values:

```text
DACQUA_SALES_AREA_MODE=allowlist
DACQUA_SALES_AREA_COUNTRY_CODE=US
DACQUA_SALES_AREA_REGION_CODES=AL,AR,AZ,CA,CO,CT,DC,DE,FL,GA,IA,ID,IL,IN,KS,KY,LA,MA,MD,ME,MI,MN,MO,MS,MT,NC,ND,NE,NH,NJ,NM,NV,NY,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VA,VT,WA,WI,WV,WY
DACQUA_SALES_AREA_LABEL="the contiguous United States and Washington, DC"
```

Production configuration remains external to immutable releases in
`/etc/dacqua-dolce/backend.env`. Do not expose unrelated secret values while
inspecting or commissioning these non-secret settings.

## Validation expectations

Regression coverage verifies that:

- the default policy contains 49 approved region codes;
- Washington, DC is eligible;
- representative contiguous states are eligible;
- Alaska and Hawaii are ineligible;
- representative U.S. territories are ineligible;
- foreign-country addresses are ineligible;
- an explicit disabled override remains possible;
- PT34 readiness rejects missing, unexpected, or wrong-country configuration.

Existing quote, order, and checkout tests continue to exercise their independent
sales-area enforcement boundaries.

## No database migration

PT35 changes business-policy configuration, readiness validation, tests, and
documentation only. It adds no database schema or data migration.

## Still deferred

PT35 does not resolve:

- tax provider or jurisdiction-specific tax rules;
- shipping-carrier availability or rating;
- shipping-insurance provider/coverage/claims terms;
- Affinity24 gateway commissioning;
- installer/service geography;
- future Alaska, Hawaii, territory, or international expansion.
