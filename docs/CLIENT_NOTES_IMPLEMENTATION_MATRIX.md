# Client Notes Implementation Matrix

Status: PT15.5 baseline
Date: 2026-09-27

This matrix is the durable boundary between client-supported requirements and implementation assumptions. New explicit client answers supersede older interpretations. Items marked **Needs Client Confirmation** or **Needs Manufacturer/Technical Verification** must not be converted into public claims or irreversible workflow decisions without new evidence.

| Area | Status | Current implementation / boundary |
| --- | --- | --- |
| Harmony pass-through naming | Implemented | Harmony / Water Conditioner / Featuring CLEAR Technology. |
| Harmony pass-through installation & ownership | Implemented | Product detail surfaces only verified pass-through facts: non-backwashing operation, no electrical power, no backwash drain, and a replaceable carbon-block prefilter. These facts are not generalized to Harmony Regenerating. |
| CLEAR customer explanation | Implemented | Describes restructuring hardness minerals into microscopic crystalline forms that are less likely to adhere as scale; does not claim hardness removal. |
| CAM terminology | Implemented | Crystal Aggregate Matrix is approved customer-facing terminology. |
| Customer Requests | Implemented | Active, Closed, All; persisted status changes and private internal notes; no inferred account relationship. |
| Accounts & Address Book | Implemented | Persisted customer identity/contact/address/order-count information. |
| Customer Inbox | Implemented | Inbox, System, Archived, All; structured system-message classification; PostgreSQL remains authoritative. |
| Welcome email | Implemented | One restrained post-verification welcome message with duplicate-send protection. |
| Pricing & Inventory | Implemented / Actionable Now | Backend-authoritative pricing and inventory exist. PT15.1 improves operational clarity without manufacturing prices or sale eligibility. |
| User Access & Roles | Implemented / Actionable Now | Persisted roles, MFA posture and privileged role management exist. Developer role remains local-only. |
| Audit Log | Implemented / Actionable Now | Privileged recent-event history exists. PT15.1 adds human-readable labels, actor email when retained user identity is available, and action/entity filtering while continuing to exclude sensitive metadata, IP addresses and user agents. |
| Recommend a System positioning | Implemented | Hero CTA enters the concise Recommend a System section. The detailed questionnaire is secondary guided assistance revealed only on request. Section language begins with `Start with your water treatment goals.` and avoids assuming homeownership or customer inexperience. |
| Recommendation-to-request language continuity | Implemented | Quote, guided-recommendation, and general-consultation prompts ask about water goals, water-use needs, source water, and installation constraints without assuming a home/household or first-time buyer. |
| Cartridge filtration public terminology | Implemented / Actionable Now | `Big Blue` remains manufacturer/internal terminology. Public system naming will use `[Family Name] Single — Cartridge Filtration` / `[Family Name] Duo — Cartridge Filtration` once the family name is approved. |
| Replacement-cartridge naming convention | Actionable Now | Use `Brand + function + micron/specification` when authoritative cartridge specifications exist. |
| Cartridge replacement guidance | Implemented | General public guidance states replacement at least every six months where applicable, with actual life varying by source-water quality, micron rating, usage, and system conditions. Harmony pass-through surfaces this guidance on its product detail. |
| Exterior-water installation guidance | Implemented | Recommend a System explains that irrigation and hose-bib lines should generally bypass treated-water equipment where appropriate, while preserving property/installation-specific judgment. |
| Conventional-softener ownership guidance | Implemented | Recommend a System advises monthly brine-salt inspection/replenishment and checking valve time-of-day after power loss where applicable, subordinate to system-specific instructions. |
| Sediment micron offerings | Needs Manufacturer/Technical Verification | Actual micron ratings to be offered remain TBD pending manufacturer confirmation. |
| Carbon-block cartridge offerings | Needs Manufacturer/Technical Verification | Actual cartridge types to be offered remain TBD pending manufacturer confirmation. |
| Cartridge gallon/service capacities | Needs Manufacturer/Technical Verification | No validated gallon/service capacities are approved for publication. |
| Customer Orders | Needs Client Confirmation | Persisted order records and backend status machinery exist; Operations remains read-only until the client confirms the operational lifecycle. |
| Payment provider | Needs Client Confirmation | Provider boundary exists; do not select or commission a provider without client direction. |
| Online purchase vs quote boundary | Needs Client Confirmation | Do not infer which products/configurations may be purchased online. |
| Installation purchasing model | Needs Client Confirmation | Do not invent installation/fulfillment commercial policy. |
| New Message composer | Needs Client Confirmation | Existing customer threads can be replied to in-app; standalone composition priority remains unresolved. |
| Custom mail filters/rules | Needs Client Confirmation | Do not add generic mail-rule complexity without a demonstrated use case. |
| Customer Request → account relationship | Needs Client Confirmation | No durable relationship exists; do not match by name, email or phone. |
| CRM assignment / priority / next action | Needs Client Confirmation | Do not add generic CRM fields without operational need. |
| Whole-house carbon family name | Needs Client Confirmation | Essence vs Clarity remains unresolved. |
| Conventional softener family name | Needs Client Confirmation | Refine vs Silken / Serene remains unresolved. |
| CLEAR acronym E/R | Needs Client Confirmation | C=Crystal, L=Lattice and A=Anti-Scale are current direction only; no final acronym expansion may be published. |
| Harmony Regenerating operation | Needs Manufacturer/Technical Verification | Exact media, cycle type, electrical/drain requirements, valve model and flow behavior remain unverified. |
| Harmony Regenerating → CLEAR relationship | Needs Manufacturer/Technical Verification / Client Confirmation | Do not infer CLEAR support from the Harmony family name. |
| Physical conditioning-component proprietary name | Needs Client Confirmation | No separate public proprietary component name has been approved. |
| Temporary calcium-magnesium bond mechanism | Needs Manufacturer/Technical Verification | Do not publish as established mechanism. |
| Exact option availability | Needs Manufacturer/Technical Verification / Client Confirmation | Optional post-filter/UV concepts must not be presented as universally purchasable until configuration applicability is verified. |
| Maintenance communication schedule | Needs Client Confirmation | Event-driven maintenance communication may be useful; cadence and product applicability remain unresolved. |

## PT15.1 governance rule

Operations surfaces should expose authoritative persisted state, authorization, and auditability clearly. They must not transform unresolved client decisions into business policy.

## PT15.2 cartridge-filtration rule

Public copy may use the confirmed Single/Duo naming structure and general six-month replacement guidance, but the application must not invent a cartridge family name, micron rating, carbon-block type, or gallon/service capacity. Those values remain manufacturer/client inputs to be added when authoritative data is available.

## PT15.2.2 recommendation-language rule

Recommendation copy should describe customer water-treatment goals and installation conditions without assuming the visitor owns a home, is new to water treatment, or has already chosen whole-house filtration as the desired outcome.

## PT15.3 product-detail ownership rule

Verified installation and ownership facts may be grouped on a product detail when they are tied to a stable known configuration. Presentation-layer facts must remain SKU-scoped when neighboring products have unresolved behavior, and authoritative catalog specifications remain the source for general technical specifications.

## PT15.4 installation-planning rule

Recommendation guidance may explain broadly applicable installation and ownership considerations when the client has confirmed them, but it must distinguish planning guidance from product specifications. Exterior-water bypass remains property-specific, and conventional-softener maintenance guidance remains subordinate to the applicable system/manufacturer instructions.


## PT15.5 recommendation-to-request continuity rule

Recommendation, product-quote, and general-consultation prompts should use neutral water-goal, water-use, source-water, and installation language. Do not reintroduce homeownership or first-time-buyer assumptions at the request/submission step.

### PT15.6 — Audience language and consultation refinement

| Client / copy direction | Classification | Implementation |
|---|---|---|
| General consultation heading: “Further improve your water” | Implemented | General consultation keeps `Talk to an Expert` as the action while the dialog heading focuses briefly on the desired outcome. |
| Use “water treatment” as the broad umbrella term where multiple treatment approaches are represented | Implemented | Hero brand copy now uses “Premium Water Treatment” and broad treatment language. |
| Avoid homeowner-only framing in general customer journeys | Implemented | Hero, consultation context, and message field language no longer assume a home/household. Product-specific “whole-home” terminology remains where technically appropriate. |
| Avoid directive consultation copy where a neutral outcome phrase or question works | Implemented | General dialog uses the brief outcome heading `Further improve your water`; helper copy no longer begins with “Tell us” or “Share.” |
| Balance performance, culinary, and wellness audience vocabulary | Implemented / ongoing copy rule | Added `docs/DACQUA_DOLCE_AUDIENCE_LEXICON.md` with 50+ terms per audience and claim-safety guidance. |


## PT15.8 guided-recommendation rule

| Client direction | Classification | Implementation |
| --- | --- | --- |
| No power or no drain -> Harmony + cartridge filtration | Implemented | Guided recommendation returns the confirmed limited-utilities starting path. |
| Power + drain + salt-free scale/deposit mitigation -> backwashing carbon + Harmony | Implemented | Guided recommendation returns the confirmed salt-free starting path. |
| Power + drain + conventionally softened water -> backwashing carbon + water softener | Implemented | Guided recommendation returns the confirmed softener starting path. |
| Softener selection must also recommend RO | Implemented | Softener result explicitly includes reverse osmosis regardless of separate RO-interest answer. |
| Detailed questionnaire placement | Implemented | The homepage keeps the concise recommendation cards primary; the structured questionnaire opens only from the `Start guided recommendation` control at the bottom of the section. |
| Future AI-chat reuse | Deferred / architecture preserved | The structured question set, recommendation context, and decision boundaries are intended to be reused by a future conversational interface rather than duplicated as separate chatbot logic. |
| Municipal vs well water | Implemented | Structured recommendation context captures source water. |
| Well water requires third-party lab testing and human review | Implemented | Well-water answers suppress automatic system recommendation and present mandatory testing/review. |
| Ask about signs of hard water, not just a hardness number | Implemented | Guided flow asks whether signs of hard water are being noticed. |
| Number of bathrooms | Implemented | Captured as structured recommendation context. |
| Number of occupants | Deferred / explicitly excluded | Client answered No; field is not present. |
| Peak-flow requirements | Needs Client Confirmation | Client answered Maybe; field is not present. |
| Chlorine/chloramine context | Implemented | Captures water-report familiarity and noticed signs of chlorine/chloramine. |
| Iron/manganese concern | Implemented | Captured as concern-oriented customer context. |
| Existing equipment | Implemented | Optional structured recommendation context. |
| Drain / electrical availability | Implemented | Used directly in recommendation branching. |
| Irrigation/hose-bib and pool/autofill | Implemented | Captured as installation context. |
| Drinking-water RO interest | Implemented | Captured as recommendation context; softener path still always includes RO. |
| Water-test results | Implemented | Captures whether results are available. |
| Neighbor/friend/family filtration experience | Implemented | Captured as recommendation context. |
| Recommendation context must remain distinct from customer message | Implemented | New structured persisted context is separate from free-form customer-authored message text. |


## PT15.9 — Product architecture normalization

Client-confirmed long-term hierarchy:

**Family → Product/System → Size/Capacity → Options/Accessories**

Implementation rules:

- `product_family` is the family layer.
- `system_type` is a separate nullable system/product-type layer and must not be inferred from a marketing name when client terminology is unresolved.
- `ProductVariant` remains the size/capacity/configuration layer, including variant-specific SKU, pricing, and inventory.
- Product-to-product option/accessory relationships are explicit and default to non-public until verified. This allows future filtration and UV options to retain their own SKU, pricing, inventory, documentation, and lifecycle rather than being flattened into free-form text.
- Do not populate unresolved names or option availability merely because the architecture can represent them.
- Essence, Clarity, Refine, Silken, and Serene remain uncommitted/reserved candidates pending further client discussion.
- Public performance claims require manufacturer confirmation.


## PT15.10 — Product configuration presentation

- Product detail pages now expose the confirmed catalog hierarchy when authoritative data exists: system variants represent size/capacity configurations, while explicitly public product relationships represent approved options/accessories.
- Variant and option/accessory sections remain absent when the catalog has no authoritative records to show.
- Creating the presentation layer does not authorize new option assignments, capacity claims, product-family names, or performance claims.
- Options/accessories must remain explicit catalog relationships and must be marked public before customer-facing presentation.


## PT15.11 — Catalog architecture in Operations

**Implemented**

- Pricing & Inventory now exposes the confirmed catalog hierarchy context alongside each governed product: family, system type, active configuration count, and count of explicitly public options/accessories.
- Missing family/system assignments remain visibly unassigned rather than being inferred from product names.
- Option/accessory counts include only relationships that are both active and approved for public presentation.
- This milestone does not create, publish, or rename any product family, system, configuration, option, or accessory.

## PT15.12 update — Options & accessories governance

| Client direction | Classification | Implementation note |
|---|---|---|
| Family → Product/System → Size/Capacity → Options/Accessories | Implemented | PT15.9 normalized the catalog model; PT15.10/11 exposed the hierarchy; PT15.12 adds privileged Operations management for explicit product relationships. |
| Verified options/accessories should be attachable without flattening them into product prose | Implemented | Relationships reference real catalog products with their own SKU/pricing/inventory lifecycle. |
| Public option/accessory presentation requires deliberate confirmation | Implemented | New relationships default to internal; privileged users must explicitly mark them public. |
| Exact UV/filter option availability per system | Needs Client / Manufacturer Confirmation | PT15.12 creates the governance workflow but does not seed or infer any relationship. |
