# PT14 Client Product Direction

This document records approved or explicitly provisional product-direction decisions from the PT14 client review. It is a decision record, not a substitute for manufacturer specifications, validated testing, certification, or final trademark review.

## Confirmed family and catalog direction

- `Harmony` is the Water Conditioner family.
- Preferred public presentation is `Harmony - Water Conditioner featuring CLEAR Technology`.
- `Origin` is the Reverse Osmosis family.
- Different capacities/configurations within one product family are variants rather than separate branded families.
- Public product presentation should lead with the family name.
- Carbon and softener family names remain unresolved. Do not assign `Essence`, `Clarity`, `Refine`, `Silken`, or `Serene` as final catalog names until the client selects them.
- Two-name family compositions remain an option, but are not approved as the current catalog convention.

## Guided selection workflow

The public site may provide a `Recommend a System` workflow, with `Help Me Choose` as supporting action language.

The approved section heading is `Start with your water treatment goals.` This avoids assuming homeownership or that the customer is new to water treatment while keeping the workflow focused on customer goals.

Initial decision paths are intentionally explanatory rather than deterministic:

1. If electrical power or a backwash drain is unavailable, begin with Harmony water conditioning plus cartridge filtration.
2. If power and drain are available and the customer wants carbon filtration plus deposit mitigation without brine-tank salt, begin with backwashing carbon filtration plus Harmony.
3. If power and drain are available and the customer specifically wants softened water, begin with carbon filtration plus a water softener.

Final recommendations must account for source-water conditions, installation requirements, water demand, and verified product capabilities.

## Cartridge housings and replacement cartridges

- `Big Blue` is retained only as a manufacturer/internal reference and is not public-facing product terminology.
- The public cartridge-filtration family name remains unresolved.
- The approved public naming structure is `[Family Name] Single — Cartridge Filtration` and `[Family Name] Duo — Cartridge Filtration`.
- Replacement-cartridge names should follow `Brand + function + micron/specification`.
- Sediment micron ratings remain TBD pending manufacturer confirmation.
- Carbon-block cartridge types remain TBD pending manufacturer confirmation.
- No validated gallon/service capacities are currently approved for publication; manufacturer confirmation is required.
- General replacement guidance is at least every six months where applicable. Actual service life varies with source-water quality, micron rating, usage, and system conditions.
- Do not invent the unresolved family name, cartridge specifications, micron ratings, cartridge types, or service-capacity claims merely to complete the catalog.

## Softener maintenance working language

Client-approved concept:

> Inspect salt every month and replenish as needed, always maintaining at minimum a 25-50% salt level by volume.

Preferred editorial form:

> Inspect the brine tank monthly and replenish salt as needed, maintaining at least approximately 25-50% salt by volume.

Treat the numeric level as working guidance until it is checked against the applicable manufacturer instructions for the final system configuration.

## Filtration and treatment claims

Avoid unsupported absolute performance language such as `removes`, `eliminates`, `100%`, or `all` when describing chemical, mineral, or contaminant treatment.

Depending on the actual treatment mechanism and supporting evidence, acceptable wording may include:

- reduces;
- helps reduce;
- targets;
- filters;
- captures;
- adsorbs;
- treats;
- helps control;
- lowers; or
- designed for reduction of.

`Reduces to near zero` is still a quantitative performance statement and must not be published unless manufacturer specifications or validated testing support it for the stated conditions.

Where available, product copy should identify the applicable manufacturer specification, validated test, or certification supporting a performance statement.

## CLEAR Technology

`CLEAR` is D'Acqua Dolce's proprietary public name for the conditioning technology/process used by Harmony.

- CLEAR is the branded terminology for the conditioning process.
- Do not use `TAC` or `Template Assisted Crystallization` in new public-facing D'Acqua Dolce copy. Existing internal identifiers, SKUs, slugs, filenames, and historical source references that contain `TAC`/`TTAC` are not renamed by this terminology decision.
- The final expansion of the `CLEAR` acronym remains unresolved.
- `Crystal Lattice` is the preferred direction for `C` and `L`.
- `Anti-Scale` is the preferred direction for `A`.
- The words represented by `E` and `R` remain unresolved.
- Do not invent or publish a final CLEAR expansion until it is approved.

Preferred customer-facing explanation:

> CLEAR restructures hardness minerals into microscopic crystalline forms so they are less likely to adhere as scale.

The current product direction is that calcium and magnesium remain in the treated water. CLEAR is not intended to claim a reduction in measured hardness concentration or conventional hardness removal. The precise physical mechanism and associated performance claims remain subject to manufacturer documentation and technical verification.

Avoid wording that says CLEAR restructures `water into a particle`. The intended subject of the restructuring language is the hardness minerals in the water.

## Crystal Aggregate Matrix (CAM)

`CAM` means `Crystal Aggregate Matrix`.

CAM is D'Acqua Dolce's customer-facing term for the microscopic crystalline form/particle associated with the CLEAR conditioning process.

Preferred terminology hierarchy:

`Harmony -> CLEAR Technology -> Crystal Aggregate Matrix (CAM)`

CAM may appear in customer-facing product copy.

The proposed description of CAM as a temporary bond between calcium and magnesium remains technically unverified. Do not publish that mechanism as an established fact until manufacturer documentation, validated testing, or other appropriate technical evidence supports it.

`Crystal Matrix Assist` is superseded by `Crystal Aggregate Matrix (CAM)` as the current working public terminology.

## CLEAR component naming

The physical distributor/component associated with CLEAR requires a separate proprietary name. That name remains unresolved and may depend on future component redesign and licensing considerations. Do not assign a public component name yet.


## PT14.4 public presentation architecture

Public presentation should separate brand hierarchy from configuration details instead of treating the complete canonical catalog name as a single display heading.

For the confirmed Harmony pass-through conditioner, the preferred hierarchy is:

1. `Harmony` — family name;
2. `Water Conditioner` — system type;
3. `Featuring CLEAR Technology` — treatment-technology label;
4. `Crystal Aggregate Matrix (CAM)` — supporting customer education for the microscopic crystalline forms described by D'Acqua Dolce.

Capacity and hardware configuration belong below this identity hierarchy as product variants/specifications when authoritative data supports them. A 1.5 cu. ft. or 2.0 cu. ft. capacity does not create a separate branded family.

The presentation layer may derive this hierarchy from a stable catalog product identifier while leaving canonical SKUs, slugs, public paths, filenames, and historical provenance unchanged.

Until the second Harmony configuration is technically verified, do not infer that `Harmony - Regenerating` uses the same CLEAR process, rename it to `Backwashing`, or publish power/drain/backwash-cycle claims for it.

Customer education may explain the approved CLEAR/CAM relationship, but must preserve the claims boundary in this document. In particular, do not publish the unresolved CLEAR acronym expansion or the proposed temporary calcium/magnesium bond mechanism as established fact.


## PT14.5 product-detail and guided-selection architecture

Product detail pages should prioritize customer decision information over internal catalog metadata. The preferred order is product identity, overview, verified technology education where applicable, the available commerce/quote action, public specifications, and finally stable product-reference information such as SKU. Raw implementation metadata such as variant counts should not receive primary customer-facing emphasis.

Public specifications must continue to come from authoritative catalog data. The presentation layer may reorganize those values for readability, but it must not manufacture, infer, or silently broaden technical claims.

Guided system selection remains a set of conversation starting points rather than a deterministic prescription. Recommendation cards should state the customer constraint or goal first, then describe the supported starting point. Final selection continues to depend on source-water conditions, installation requirements, water demand, and verified product capabilities.

SKU-specific presentation rules are claims boundaries as well as visual rules. CLEAR/CAM education is currently assigned only to `DD15CAT-TTACPTV`; it must not be inferred for `DD15CAT-TTACRV` or another product without authoritative support. Unresolved family naming for carbon and softener products must likewise not be promoted or normalized by the derived presentation layer.


## PT14.6 customer-request journey

Product-specific quote requests must continue to persist the selected product through the existing structured `product_id` relationship. The customer-facing dialog may explain that association, but must not duplicate product identity into customer-authored message text.

Guided-selection and general-consultation inquiries remain unassociated with a product until a product is actually selected. Presentation context may distinguish those entry points while the dialog is open, but transient UI context must not be silently encoded into the customer's message. If durable inquiry-source attribution becomes a business requirement, add an explicit structured field and migration rather than overloading free-form customer content.

Request forms should collect only useful response context. Encourage customers to describe water goals or concerns, source water when known, water-use needs, and installation constraints without requiring technical knowledge they may not have. Form state should reset between inquiries so details from a previous request are not carried into a later one.


## PT14.7 Operations customer-request workspace

Customer Requests should present the existing request data as an employee workspace rather than as an undifferentiated card. Keep customer identity/contact information, customer-authored request text, private internal follow-up notes, and lifecycle status visually distinct. Customer-authored content and private employee notes must never be presented as though they are the same content source.

The existing request lifecycle remains authoritative: `new`, `contacted`, `quoted`, and `closed`. The Operations UI may render those values as human-readable labels (`New`, `Contacted`, `Quoted`, `Closed`) without changing persisted enum values or backend behavior. Active/Closed/All filtering and reopening through a status change remain unchanged.

A request with no associated `product_id` remains a `General consultation`. Do not infer whether it originated from Help Me Choose or another transient frontend entry point because PT14.6 deliberately does not persist that attribution.

PT14.7 intentionally does not add assignment, priority, next-action dates, lead scoring, or other CRM fields. Add durable workflow fields only after real operational use establishes a concrete persistence requirement; when needed, model them explicitly rather than encoding them in customer messages or private notes.


## PT14.8 Operations accounts and address-book workspace

Accounts & Address Book should present registered customer identity, contact information, account status, saved addresses, and genuinely persisted customer relationships as an employee reference workspace. Address labels and default shipping/billing designations remain authoritative customer-saved data and should be visually easy to distinguish.

The existing order relationship is durable because orders store the registered customer identity; Operations may therefore summarize recorded order counts by customer ID. Quote/customer-request records do not currently store a customer user ID, so the UI must not manufacture an account relationship by matching names, email addresses, or phone numbers. General and product-specific requests remain in Customer Requests until an explicit durable relationship is modeled.

PT14.8 remains read-only and migration-free. It does not add customer editing, address editing, CRM ownership, inferred lead history, or duplicated account data. Add write workflows and new relationships only when the business requirement and authorization/audit boundaries are defined explicitly.


## PT14.9 communications classification and customer welcome

Customer Inbox is the employee working mailbox, not a flat rendering of every archived delivery. Application-generated account mail must remain durably archived while being separated from normal customer correspondence through structured delivery provenance. `email_verification`, `password_reset`, and `customer_welcome` are System mail; do not classify them by matching subject keywords.

The mailbox presents explicit Inbox, System, Archived, and All views with visible counts. Inbox is open human/customer correspondence requiring normal attention. System retains application-generated transactional/lifecycle mail. Archived remains an employee-controlled conversation lifecycle state, while All remains the complete authoritative archive. Search operates within the selected visible view rather than silently changing classification.

After successful email verification, send one welcome/next-step message inviting the customer to explore water-filtration solutions or use Help Me Choose. The welcome is event-driven rather than a recurring promotional drip and is archived as `customer_welcome`. Duplicate welcome delivery for the same user must be prevented through the structured email-delivery record.

Operations should keep employee communication inside the D'Acqua Dolce web application. Do not use `mailto:` links in Operations; existing conversations use the in-app reply workflow, while standalone customer email addresses provide a Copy email action until an intentional in-app new-message composer exists.


## PT15.3 Harmony pass-through ownership presentation

The confirmed Harmony pass-through configuration may present its verified installation and ownership characteristics together on the product-detail page: non-backwashing operation, no electrical power requirement, no backwash-drain requirement, and a replaceable carbon-block prefilter. These facts apply only to the known pass-through SKU and must not be generalized to Harmony Regenerating or other products without authoritative support.

Where a replaceable cartridge is known to apply, public ownership guidance may state replacement at least every six months where applicable, while making clear that actual service life varies with source-water quality, micron rating, usage, and system conditions. Do not publish an unverified micron rating, carbon-block type, or gallon/service capacity.

The product-detail overview should prefer the verified presentation-layer summary when one exists so that the customer sees the same approved claims boundary on the catalog card and detail page.


## PT15.4 installation planning and ownership education

The Recommend a System experience may include general planning guidance that helps customers understand ownership implications without treating those points as SKU specifications.

Exterior irrigation and hose-bib lines should generally bypass treated-water equipment where appropriate so large exterior demand is not treated unnecessarily. This is planning guidance rather than a universal plumbing rule; final routing depends on the property and installation.

For conventional water softeners, public ownership guidance may advise customers to inspect brine-tank salt about monthly, replenish it as needed, and verify valve time-of-day after a power loss where applicable. System-specific manufacturer instructions remain authoritative.

These planning notes must not resolve the still-unapproved softener family name or imply that every property, valve, or installation is configured identically.


## Recommendation-to-request language continuity

Customer-facing recommendation, consultation, and quote-request copy should remain neutral about property ownership and customer experience level. Ask for water goals, source-water context, water-use needs, and installation constraints rather than assuming a `home`, `household`, or first-time buyer.

This language rule applies across the recommendation-to-request handoff so the conversion step does not reintroduce assumptions removed from the recommendation experience.

## PT15.6 — Audience language and consultation refinement

Confirmed copy direction from the 2026-09-27 refinement pass:

- Use **water treatment** as the broad umbrella term when a surface spans conditioning, softening, filtration, reverse osmosis, or other treatment approaches.
- Avoid narrowing general brand/consultation copy to homeowners unless the context is specifically residential.
- Avoid unnecessarily directive consultation prompts such as “Tell us…” or “Share…” when a concise outcome phrase, friendly question, or neutral helper sentence works.
- Current general consultation heading: **“Further improve your water”**
- Deliberately vary audience-signaling vocabulary across performance, culinary, and wellness contexts instead of repeating “goals” throughout the experience.
- `docs/DACQUA_DOLCE_AUDIENCE_LEXICON.md` is the working copy reference for this vocabulary strategy.



## PT15.8 structured recommendation logic

The client confirmed the three current municipal-water starting paths:

1. If electrical power or a backwash drain is unavailable, start with Harmony conditioning plus cartridge filtration.
2. If power and drain are available and the customer prefers carbon filtration with scale/deposit mitigation without salt, start with backwashing carbon plus Harmony.
3. If power and drain are available and the customer prefers conventionally softened water, start with backwashing carbon plus a water softener. Reverse osmosis must also be recommended whenever the softener path is selected.

The guided recommendation may ask about municipal versus well water, signs of hard water, number of bathrooms, whether the customer has read the water-quality report supplied with the water bill, signs of chlorine/chloramine, iron/manganese concerns, existing equipment, drain and electrical availability, irrigation/hose-bib plumbing, pool/autofill plumbing, drinking-water RO interest, available water-test results, and whether neighbors/friends/family use water filtration.

Do not ask for number of occupants. Peak-flow requirements remain unresolved (`Maybe`) and should not be added as a required recommendation question yet.

If the customer identifies the source as well water, third-party laboratory testing is mandatory. The application must not produce an automatic system recommendation for well water; route the inquiry to human review/testing instead. Ambiguous source-water, utility, or treatment-preference answers may likewise fall back to human review rather than fabricating certainty.

Recommendation answers are structured request context, not customer-authored message text. Persist them separately so Operations can inspect the recommendation basis without altering the customer's free-form message.

The detailed guided questionnaire is **secondary assistance**, not the primary homepage presentation. Keep the concise `Recommend a System` starting-point cards visible, and reveal the questionnaire only after the customer explicitly asks for guided assistance.

Treat the question set, structured recommendation context, and decision rules as reusable domain logic. A future AI chatbot may ask the same questions conversationally; it should reuse the same underlying context and recommendation boundaries rather than maintain a separate recommendation policy.


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


## PT15.11 operations/catalog governance rule

The employee Pricing & Inventory workspace should reflect the same confirmed product architecture used by the public catalog: Family → Product/System → Size/Capacity → Options/Accessories. Employees should be able to see whether family/system metadata is assigned and how many active configurations/public options currently exist, without the UI inferring missing terminology or treating private/unconfirmed relationships as public.

## PT15.12 — Product option/accessory governance

The confirmed Family → Product/System → Size/Capacity → Options/Accessories architecture now has an employee-facing governance path in Operations.

- Product relationships remain explicit catalog records rather than free-form copy.
- Newly created relationships begin as internal/non-public.
- A privileged employee must deliberately make a relationship public after compatibility and public presentation have been confirmed.
- Removing or changing a relationship is audit-backed.
- This capability does not itself confirm that any particular UV, filtration, or other accessory is compatible with a product.
- Unresolved family/system terminology remains outside this workflow.
