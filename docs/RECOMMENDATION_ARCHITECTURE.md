# D'Acqua Dolce Recommendation Architecture

## Purpose

D'Acqua Dolce uses one authoritative recommendation policy for guided web assistance and future conversational interfaces. Presentation layers may differ, but recommendation rules must not be reimplemented independently in the frontend, an AI chatbot, or employee tooling.

## Authoritative decision boundary

`backend/app/services/recommendations.py` owns the deterministic starting-path rules currently confirmed by the client.

The service accepts a structured `RecommendationContext` and returns a structured `RecommendationDecision` containing:

- stable decision code;
- customer-facing title and explanation;
- whether human review is required;
- whether third-party laboratory testing is required;
- stable component identifiers for the recommended starting path;
- sizing-readiness metadata showing whether bathrooms, occupants, and water-service pipe size have been captured.

The public guided form calls this service through `POST /api/quotes/recommendation`.

A future AI/chat interface should call the same backend contract rather than recreate these rules in prompts or client-side branching.

## Policy versioning

`RECOMMENDATION_POLICY_VERSION` identifies the policy revision used to create a recommendation snapshot.

When a guided request is submitted, the server evaluates the submitted context again and stores:

- the original structured recommendation context;
- the exact recommendation decision returned at submission time;
- the recommendation policy version.

The server-side re-evaluation is intentional. The persisted decision must not trust a browser-supplied recommendation result.

Historical requests therefore remain interpretable even after recommendation rules change. Operations should display the stored snapshot, not silently re-run current rules against historical answers.

Requests created before decision snapshots existed may have recommendation context without a decision snapshot. Operations labels these as legacy guided requests and requires manual review.

## Current confirmed rules

The current policy implements only confirmed client direction:

1. Well water -> mandatory third-party laboratory testing and human review; no automatic system recommendation.
2. Unknown source water -> human review.
3. Municipal water with no electrical power or no drain -> Harmony + cartridge filtration.
4. Municipal water with uncertain power/drain availability -> human review.
5. Municipal water with power + drain and salt-free preference -> backwashing carbon + Harmony.
6. Municipal water with power + drain and conventional softening preference -> backwashing carbon + water softener + reverse osmosis.
7. Municipal water with power + drain and unresolved treatment preference -> human review.

The service intentionally does not infer unresolved family names, capacities, option compatibility, contaminant performance, or manufacturer claims. Recommendation policy v2 may report that sizing inputs are complete, but it must keep `capacity_recommendation_available=false` until authoritative size-selection thresholds are supplied and validated.

## Operations triage

Operations receives the immutable recommendation snapshot with each Customer Request.

The workspace provides separate views for:

- all requests in the selected lifecycle view;
- guided requests;
- guided requests requiring human review;
- guided requests requiring third-party laboratory testing.

Open lab-testing requests take precedence in the Operations next-action summary because the client has defined testing as mandatory for well water.

The recommendation result is visually separate from:

- customer-authored request text;
- submitted questionnaire context;
- private employee follow-up notes.

## Communications

Customer acknowledgement emails remain restrained and do not make additional technical promises.

Operator notifications include the stored recommendation result, policy version, review/testing flags, components, and submitted context so staff can triage without reconstructing the decision manually.

## Future chatbot integration

A future AI assistant may collect the same structured fields conversationally, but it should:

1. map conversation answers into `RecommendationContext`;
2. call the authoritative backend evaluator;
3. present the returned decision without changing its business meaning;
4. submit the same structured context through the normal Customer Request pathway when the customer chooses to continue;
5. preserve mandatory human-review and laboratory-testing boundaries.

The model may explain terminology conversationally, but it must not bypass or override deterministic business/safety rules.

## Change discipline

When client direction changes:

1. update the backend policy and tests;
2. increment `RECOMMENDATION_POLICY_VERSION`;
3. update this document and the Client Notes Implementation Matrix;
4. preserve historical stored snapshots;
5. avoid backfilling old decisions unless a deliberate migration/review process is approved.
