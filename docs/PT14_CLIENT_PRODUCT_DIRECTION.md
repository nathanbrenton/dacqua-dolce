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

Initial decision paths are intentionally explanatory rather than deterministic:

1. If electrical power or a backwash drain is unavailable, begin with Harmony water conditioning plus cartridge filtration.
2. If power and drain are available and the customer wants carbon filtration plus deposit mitigation without brine-tank salt, begin with backwashing carbon filtration plus Harmony.
3. If power and drain are available and the customer specifically wants softened water, begin with carbon filtration plus a water softener.

Final recommendations must account for source-water conditions, installation requirements, household demand, and verified product capabilities.

## Cartridge housings and replacement cartridges

- `Big Blue` is retained only as a manufacturer/internal reference.
- The public replacement-cartridge housing family name is unresolved.
- Single and Duo housing configurations are planned.
- Replacement cartridges may include sediment variants by micron rating and carbon-filter variants.
- Public housing and cartridge names must not be invented or normalized into the canonical catalog until approved.

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

Guided system selection remains a set of conversation starting points rather than a deterministic prescription. Recommendation cards should state the customer constraint or goal first, then describe the supported starting point. Final selection continues to depend on source-water conditions, installation requirements, household demand, and verified product capabilities.

SKU-specific presentation rules are claims boundaries as well as visual rules. CLEAR/CAM education is currently assigned only to `DD15CAT-TTACPTV`; it must not be inferred for `DD15CAT-TTACRV` or another product without authoritative support. Unresolved family naming for carbon and softener products must likewise not be promoted or normalized by the derived presentation layer.


## PT14.6 customer-request journey

Product-specific quote requests must continue to persist the selected product through the existing structured `product_id` relationship. The customer-facing dialog may explain that association, but must not duplicate product identity into customer-authored message text.

Guided-selection and general-consultation inquiries remain unassociated with a product until a product is actually selected. Presentation context may distinguish those entry points while the dialog is open, but transient UI context must not be silently encoded into the customer's message. If durable inquiry-source attribution becomes a business requirement, add an explicit structured field and migration rather than overloading free-form customer content.

Request forms should collect only useful response context. Encourage customers to describe water goals or concerns, source water when known, household needs, and installation constraints without requiring technical knowledge they may not have. Form state should reset between inquiries so details from a previous request are not carried into a later one.
