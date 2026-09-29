# Client Notes Implementation Matrix

Status: PT15.5 baseline
Date: 2026-09-27

This matrix is the durable boundary between client-supported requirements and implementation assumptions. New explicit client answers supersede older interpretations. Items marked **Needs Client Confirmation** or **Needs Manufacturer/Technical Verification** must not be converted into public claims or irreversible workflow decisions without new evidence.

| Area | Status | Current implementation / boundary |
| --- | --- | --- |
| Harmony pass-through naming | Implemented | Harmony / Water Conditioner / Featuring CLEAR Technology. |
| Harmony pass-through installation & ownership | Implemented / updated | Product detail retains verified non-backwashing/no-power/no-drain facts. The superseded always-included carbon-block prefilter claim is removed; preferred pairing is now Duo cartridge filtration with replaceable sediment + carbon filters. |
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
| Whole-house carbon family name | Implemented | `Essence` is confirmed and applied to existing whole-house carbon catalog records. |
| Conventional softener family name | Confirmed / awaiting product data | `Refine` is confirmed; no SKU is invented until authoritative softener product data exists. |
| CLEAR public acronym | Implemented | Approved expansion: `Crystal Lattice Enabling Anti-Scale Reduction`. `Reduction` must not be presented as conventional hardness/mineral removal. |
| Harmony Regenerating operation | Needs Manufacturer/Technical Verification | Exact media, cycle type, electrical/drain requirements, valve model and flow behavior remain unverified. |
| Harmony Regenerating product | Implemented / retired | Removed from the offered lineup; historical record retained inactive. Future combined conditioner + carbon concept remains TBD. |
| Physical conditioning-component proprietary name | Implemented | `CAM Induction` is approved as the public name for the internal conditioning component associated with CLEAR. The name does not establish an unverified physical mechanism. |
| Temporary calcium-magnesium interaction mechanism | Needs Manufacturer/Technical Verification | Client can provide supporting documentation. Do not publish as established mechanism until that documentation is reviewed and accepted. |
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
| Number of occupants | Implemented / superseding direction | Newer client direction says capacity sizing should use occupants; guided context now captures the count when known. |
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
- Essence and Refine are now confirmed family names. Clarity, Silken, and Serene remain uncommitted/reserved candidates pending further client discussion.
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


## PT16.1 — Recommendation decision service

**Implemented**

- The confirmed guided-recommendation branching now lives in one backend decision service rather than only inside the React presentation layer.
- The service returns stable machine-readable decision codes, structured treatment-component identifiers, human-review status, and the mandatory third-party-lab boundary for well water.
- The homepage guided questionnaire consumes that backend decision service.
- Future conversational/AI interfaces should consume the same recommendation endpoint/service rather than reimplementing the rules in prompt text or frontend code.
- Recommendation context fields that do not currently affect branching remain preserved as structured consultation context; they must not silently become decision rules without client confirmation.

## PT16.2 — Recommendation case intelligence & Operations triage

**Implemented**

- Guided recommendation submissions are re-evaluated on the server at request-creation time; the browser cannot author the authoritative stored decision.
- Each guided request stores an immutable recommendation decision snapshot and recommendation-policy version alongside the original structured context.
- Historical recommendation snapshots are displayed as submitted rather than silently re-evaluated under newer policy rules.
- Existing/legacy guided requests that predate decision snapshots remain valid and are explicitly identified for manual review.
- Operations exposes guided, human-review, and mandatory-lab-testing triage views while preserving the existing Active / Closed / All lifecycle views.
- Open guided requests requiring third-party laboratory testing receive highest recommendation-related priority in the Operations next-action summary.
- Operator notification email includes the stored recommendation result, policy version, review/testing flags, component identifiers, and submitted recommendation context.
- Recommendation results, customer-authored messages, structured questionnaire context, and private employee notes remain separate information boundaries.
- `docs/RECOMMENDATION_ARCHITECTURE.md` is the rebuild/development reference for web and future AI/chat recommendation reuse.


## PT16.3 — Catalog & product-line reconciliation

| Client direction | Classification | Implementation |
| --- | --- | --- |
| Essence = whole-house carbon family | Implemented | Existing carbon catalog records use `Essence` as family; backwashing configuration is presented as `Essence - Backwashing`. |
| Refine = conventional softener family | Confirmed / deferred catalog creation | Name is reserved for the softener line; no softener SKU/product is fabricated. |
| Harmony - Regenerating removed from lineup | Implemented | Canonical catalog marks the record inactive and a migration retires the existing production row while retaining history. |
| One product page with size variants | Implemented architecture / sizing inputs captured | Existing `ProductVariant` layer remains the capacity/configuration mechanism. Bathrooms, occupants, and water-service pipe size are now captured, while actual capacity thresholds remain deferred pending authoritative rules. |
| Harmony preferred pairing = Duo sediment + carbon cartridge filtration | Implemented as presentation guidance | Removed the superseded always-included carbon-block prefilter claim; no unverified Duo SKU/family is fabricated. |
| UV for Harmony | Confirmed direction / awaiting catalog product data | Relationship architecture exists; no public relationship is created until an authoritative UV product record exists. |
| Calcium/magnesium mechanism documentation | Needs Manufacturer/Technical Verification | Client says documentation can be supplied; mechanism remains unpublished until reviewed. |

## PT16.4 CLEAR / CAM terminology rule

Public Harmony education may spell out `CLEAR` as `Crystal Lattice Enabling Anti-Scale Reduction`, retain `CAM = Crystal Aggregate Matrix`, and name the internal conditioning component `CAM Induction`. These terminology approvals do not broaden performance claims: calcium and magnesium remain in treated water, measured hardness reduction is not claimed, and the proposed temporary calcium/magnesium interaction remains unpublished pending technical documentation.


## PT16.5 — Recommendation sizing inputs & capacity readiness

| Client direction | Classification | Implementation |
| --- | --- | --- |
| Size recommendation should consider bathrooms | Implemented input | Existing structured bathroom field participates in sizing-readiness assessment. |
| Size recommendation should consider occupants | Implemented input | New optional numeric occupant field supersedes the earlier exclusion. |
| Size recommendation should consider water-service pipe size | Implemented input | New optional free-text service-pipe field captures known field data without inventing a constrained size list. |
| Actual 1.5 / 2.0 cu. ft. sizing thresholds | Needs Manufacturer/Technical Verification | Backend explicitly reports that capacity recommendation is unavailable until verified rules are supplied. |
| Peak-flow requirement | Needs Client Confirmation | Still `Maybe`; not made a required sizing input. |

## PT16.6 — Ownership & communication foundation

| Client direction | Classification | Implementation |
| --- | --- | --- |
| Pool-fill lines generally bypass treatment when practical | Implemented guidance | Recommendation/account ownership guidance now includes pool-fill with irrigation/hose-bib bypass and explains filtration-media service-life rationale. |
| Softener monthly salt inspection/replenishment | Implemented conservatively | Public guidance keeps the monthly check/replenish direction; universal 25–50% numeric minimum remains withheld pending manufacturer confirmation. |
| Verify valve time after power interruption for softener + backwashing carbon | Implemented guidance | Both equipment categories are named in ownership guidance. |
| Emphasize Help Me Choose | Implemented | Guided-question CTA uses `Help Me Choose`; direct expert assistance remains an alternative. |
| Direct online purchase of complete systems | Confirmed / commerce roadmap | Existing commerce boundary remains; initial launch requirement is equipment-only with installation arranged separately. |
| Certified-installer / location-dependent installation later | Deferred | Preserve as later-stage capability; do not imply installer-network availability today. |
| Maintenance information in customer account | Implemented foundation | Account includes a Maintenance & Support panel with confirmed generic guidance. |
| Optional maintenance/follow-up emails chosen by customer | Implemented preference foundation | Persisted opt-in preferences default off; actual reminder scheduling remains deferred until installed-product/service-date data exists. |
| Filter / softener / UV / annual / product-specific reminder preferences | Implemented preference foundation | Customer can explicitly enable each category. |
| Post-purchase + post-installation follow-up | Implemented preference foundation | Separate opt-ins are persisted; actual event scheduling remains deferred. |
| Welcome email | Existing behavior retained | Keep one restrained post-verification welcome message; no drip campaign. |
| Customer Inbox System separation | Existing behavior retained | Structured system mail remains outside normal employee Inbox but inside authoritative archive. |
| Employee persistent filters | Deferred | Client delegated judgment; insufficient operational need today. |
| Employee new-message composer | Deferred | Client remains unsure; existing in-app reply workflow remains primary. |
| Signed-in Customer Request → account relationship | Implemented and surfaced | Request creation already stores authenticated `user_id`; account now exposes the customer's own request history using that durable relationship. |
| Manuals/downloads + QR maintenance access | Deferred | Requires authoritative product/installed-equipment documentation and identifiers. |


## PT16.7 ownership / maintenance foundation

| Client direction | Classification | Implementation |
|---|---|---|
| Maintenance information in customer account | Implemented | Installed equipment now appears alongside generic ownership guidance. |
| Product-specific maintenance reminders | Foundation implemented | Equipment ownership/service dates are persisted; reminder delivery remains deferred until authoritative product schedules exist. |
| Downloadable/manual documentation | Implemented where authoritative documents exist | Public active product documents are surfaced from recorded customer equipment. |
| QR code on/near installed equipment | Deferred | Equipment records now provide a durable future target, but no QR workflow is invented before physical labeling/support requirements are defined. |
| Product service history / schedule | Actionable foundation | Installation, last-service, and next-service dates can be recorded by privileged Operations staff. |

## PT16.9 — Catalogue, availability, and latest client feedback

| Client direction | Classification | Implementation |
| --- | --- | --- |
| Product/catalogue + visual/branding are next priorities | Active priority | This milestone focuses on catalogue correctness and customer-facing availability presentation; speculative CRM/order workflow expansion remains deferred. |
| Harmony Regenerating removed | Already implemented / revalidated | Canonical catalog retains only an inactive historical record; it is not offered publicly. |
| Refine Pass-Through removed | Reconciled | `Refine` remains reserved for the conventional softener family. The legacy seed script no longer mislabels the carbon pass-through SKU as Refine; the carbon line remains `Essence`. |
| Refine Regenerating description inaccurate | Publication guardrail | No Refine softener SKU is published until authoritative product data/copy exists. The legacy carbon SKU is reconciled to `Essence - Backwashing` rather than publishing inaccurate Refine copy. |
| Out of stock + estimated lead time | Implemented foundation | Product inventory can store an optional customer-facing lead-time string. Out-of-stock/backordered inventory remains visible even when a product is quote-only. |
| Notify When in Stock | Implemented consent foundation | Customers may register an email against an out-of-stock product. The subscription is stored idempotently; no automatic notification job is commissioned yet. |
| Customer product documents | Architecture expanded | Document taxonomy now supports specification sheet, owner’s manual, installation guide, maintenance guide, warranty, service schedule, and water-test/report information. Documents still require authoritative files before publication. |
| Affinity 24 payment provider | Selected direction / integration deferred | Record as the selected provider direction. No production checkout integration is commissioned until provider API/hosted-payment documentation, credentials, verification, and sandbox path are reviewed. |
| Positive website language | Site-wide principle | Prefer positive/results-oriented language, but clarity and technical accuracy take precedence over mechanically avoiding negative words. |
| Sales follow-up features | Deferred pending discussion | Do not invent CRM workflow because the client does not yet understand the choices. |
| Pricing & Inventory future scope | Deferred pending discussion | Retain existing authoritative pricing/inventory controls; do not broaden scope from an unanswered questionnaire item. |
| Customer order statuses | Deferred pending explanation | Existing order model remains unchanged until the client understands the operational status choices and actual fulfillment workflow. |

## PT17 — Catalog, Operations, and responsive typography refinement

| Client direction | Classification | Implementation |
| --- | --- | --- |
| Product/catalogue + visual/branding are next priorities | Implemented milestone | PT17 focused on public catalog clarity, product presentation, Operations attention workflow, and typography/visual consistency rather than speculative CRM/payment expansion. |
| Preserve confirmed Harmony / Essence / Origin architecture | Implemented / revalidated | Product presentation and supporting seed/catalog wording were refined without inventing missing Refine softener data. |
| Do not publish unverified Harmony mechanism claims | Implemented guardrail | Superseded temporary mechanism wording remains withheld pending authoritative manufacturer/technical documentation. |
| Make Operations attention area more compact and immediately actionable | Implemented | PT17.1 converted the metric area into a compact clickable dashboard that navigates to the relevant section and, where possible, the first matching item requiring attention. |
| Smallest typography should be larger across all font choices | Implemented | PT17.2 raised the small/medium readability floor while preserving the established large-display hierarchy. |
| Greater font variety for small/medium roles using luxury/performance/culinary/wellness direction | Implemented | PT17.3 introduced semantic typography recipes with distinct body/UI/label/data font roles and controlled casing/tracking behavior. |
| Responsive typography changes should remain uniform/proportional/transparent across fonts | Implemented | PT17.4 centralized shared responsive size tiers; typography recipes control style but no longer independently control responsive font-size hierarchy. |
| Large H1/hero tier should remain consistent across fonts | Implemented guardrail | PT17.4 re-established a shared large-display ceiling after visual review showed perceptual inflation in sans-heavy selections. |
| Theme/font review by client | Client review requested | Client follow-up list includes a friendly request to try Light/Dark appearance, themes, and typography choices and identify preferred or unsuitable combinations. |

**PT17 status: CLOSED.**

Production validation completed at runtime revision `ce8f92ff2e60e06fc8e6de809f29828695723ce9`, release `/srv/dacqua-dolce/releases/20260928T072624Z`. The next milestone should continue only from confirmed product/business data and client feedback rather than extending PT17 opportunistically.

## PT19.1 — Assisted-sales intake gate

| Client direction | Classification | Implementation |
| --- | --- | --- |
| First 20+ whole-house system sales require employee/customer interaction | Implemented policy boundary | Recommendation policy v3 keeps guided system selection as a starting path and marks every current recommendation for staff review before purchase. Historical decision snapshots retain their original policy version. |
| Collect ZIP/service-area context before recommendation | Implemented intake | Guided recommendations capture an optional service ZIP; the final inquiry dialog requires service ZIP so product-specific and general system inquiries also preserve it in structured recommendation context. |
| Collect hardness, chlorine/chloramine, iron/manganese, and pH when known | Implemented optional structured context | The recommendation context now accepts known hardness text (with customer-supplied units), optional chlorine/chloramine and iron/manganese details, and pH constrained to 0–14. Unknown measurements remain valid and do not block inquiry submission. |
| Household size and bathrooms matter | Revalidated / strengthened | Existing structured inputs remain part of sizing readiness; the final inquiry dialog also captures them so a customer can submit useful basics without first completing the full guided questionnaire. |
| Well water requires employee interaction and third-party laboratory results | Revalidated hard boundary | Well-water requests continue to produce `well_testing_required`, require staff review, and require third-party lab results before D'Acqua Dolce makes a final system recommendation. |
| Irrigation/pool/exterior routing and existing equipment matter | Revalidated | Existing guided fields remain authoritative recommendation context and flow into the immutable request snapshot reviewed by Operations. |
| Ask whether neighbors/friends/family use filtration and why | Implemented as optional research context | Existing tri-state network-use input is supplemented by optional free-text context. It is stored with the inquiry but does not alter the technical recommendation algorithm. |
| Use early assisted sales to improve education/recommendation logic | Architecture preserved | Recommendation inputs and server-authored decision snapshots remain versioned so observed gaps can drive later policy revisions without rewriting historical requests. |
| Direct whole-house checkout | Explicitly deferred | PT19.1 does not enable self-service whole-house checkout. Formal quote creation/approval is the next assisted-sales dependency; payment remains downstream of an approved quote. |
