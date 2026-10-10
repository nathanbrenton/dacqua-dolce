# PT36 — Production read-only evidence exercise: acceptance record

## Purpose

Record the bounded, non-authorizing production host inspection used to test the PT33-B v0.5 resource-verification pipeline before extracting an independently deployed `business-template` repository. This record describes the tested procedure and its limits, not a certification that any resource is available for a future business.

The **only manifest used** was `docs/production/pt33/business-manifest.example.json` for the synthetic `sample-business-staging` instance. It is not a proposed, approved, or provisionable business. The PT33 planner validated it against the schema at the `f2ce9b7` development checkpoint using the full 40-character Git revision.

## Accepted observations

1. The five-file, standard-library-only PT33 Debian collection bundle was checked with SHA-256 on the production host. Local PT33 tests passed **86/86**.
2. An unprivileged Debian 13 collection as the existing SSH user inspected visible Unix users/groups and UID/GID values, installed/loaded systemd unit names, listening TCP ports/bindings, and **only** the three filesystem paths proposed in the synthetic manifest. No NGINX or PostgreSQL opt-ins were enabled in this first collection. All available inventory sections were marked **partial**; the NGINX and PostgreSQL sections were **unsupported**.
3. The private host evidence was transferred outside the public Git repository and accepted by the offline integrated verifier. The synthetic assessment contained **0 observed collisions**, **10 unverified checks**, and **0 entries classified as not observed**. These figures do **not** establish availability, since observations were partial or unsupported.
4. A separately reviewed administrative metadata helper was tested locally (**11/11 mocked tests**), transferred with matching SHA-256, and approved for a narrow read-only production execution. It ran under the ordinary SSH user and invoked only an NGINX configuration inspection and two PostgreSQL system-catalog name queries through noninteractive `sudo` as needed. It did not run the entire PT33 collector with elevated privileges.
5. The supplemental report recorded **partial** observations of NGINX server-name identifiers and PostgreSQL database/role names; its three section digests passed verification on the host. Its output was a privately owned, mode-`0600` file. Subsequent service checks showed NGINX and PostgreSQL **active**. This does not constitute continuous availability monitoring or a guarantee of zero impact.
6. An offline comparison against the **synthetic** manifest found **0/1 exact database-name matches**, **0/2 exact role-name matches**, and **0/1 exact NGINX server-name matches** in the supplemental partial inventories. This is **not** a clearance or an assurance of uniqueness; wildcard, default-server and effective routing behavior, other database clusters, and unobserved resources remain unresolved.

## Trust and disclosure boundaries

- `ready_to_apply=false` was retained in the baseline host snapshot, the supplemental administrative metadata report, and the offline assessment. The workflow contains **no authorization to deploy or provision**.
- SHA-256 list digests provide integrity checks for recorded values, **not independent authentication of the host or collector**. The host label is self-reported and must be corroborated through trusted SSH/operations records. Evidence freshness is bounded by the verifier's explicit policy, not proof of future availability.
- The administrative report is **supplemental evidence with a different privilege provenance**. It must not be silently merged into the original PT33 evidence or presented as a single exhaustive snapshot. Status `partial` is never upgraded to `complete` solely because a command succeeded.
- NGINX `-T` processes full configuration in memory and can encounter secret-bearing directives; no raw configuration should be printed, logged, exported, or committed. The reviewed helper's output-size check occurs after subprocess capture; a hard in-flight memory bound is not established.
- PostgreSQL inspection covers name metadata in **one accessible local cluster**, not all clusters, ownership/privilege relationships, or customer tables. The Unix account used for the unprivileged collection had no matching PostgreSQL role; no role or privilege was created to circumvent that fact.
- The privately stored original host evidence, administrative report, and synthetic assessment remain **outside the Git repository**. Do not commit actual host inventories, customer data, credentials, environment files, database URLs, or raw NGINX configuration.

## Remaining gates before independent-business provisioning

A **real, reviewed business manifest** and its own server/account deployment design are still required. Confirm allocations and possible collisions for Unix identities, systemd units and drop-ins, filesystems/mounts, TCP bindings and reserved ports, NGINX active/effective routing and TLS, PostgreSQL cluster/role ownership and privileges, DNS, firewall, backups/restores, and monitoring. Separately verify ownership, billing, recovery, and offboarding for every external provider. Never infer third-party account independence from a host snapshot.

A passing PT36 synthetic exercise is a pipeline test, **not** certification of available identifiers. Continue to protect the existing D'Acqua Dolce production stack, keep `ready_to_apply=false`, and require separate, explicit change authorization before any provisioning or deployment.

## Development checkpoint and template extraction

At the start of PT36, the committed application repository checkpoint was `f2ce9b7` (`main` synchronized with `origin/main`). The PT36 helper and documentation were **local uncommitted additions** during this exercise; no later commit is asserted here. The source-to-template work should create a separate repository at `~/Desktop/business-template/`, not place version-controlled source beneath `~/Desktop/dacqua-dolce_build-assets/`. The latter remains an offline dependency/test-asset store. A new template must have its own root `LICENSE`, independent Git history, sanitized examples, and separate identity/secret/provider boundaries.

## Release checklist

- [x] PT33 original read-only collection and offline integrated evaluation exercised on Debian production.
- [x] Supplemental administrative metadata inspection exercised after separate approval.
- [x] NGINX and PostgreSQL checked active following the supplemental inspection.
- [x] Synthetic partial-inventory comparison documented without resource-allocation claims.
- [ ] Independently validate transferred supplemental evidence digests and host label on the local workstation (if not already separately verified).
- [ ] Review and accept the complete PT36 source/documentation diff before an explicitly authorized Git commit/push.
- [ ] Define and verify an actual independent-business resource manifest and external account ownership before allocation.

This acceptance record deliberately excludes sensitive inventory values and must not be interpreted as a release or deployment authorization.
