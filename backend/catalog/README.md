# Production catalog bootstrap

`production_catalog.json` is the canonical rebuild-grade baseline for public
D'Acqua Dolce product metadata.

It intentionally contains only seed-owned catalog metadata:

- manufacturer metadata;
- product categories;
- products identified by stable SKU and slug;
- product image metadata;
- verified product specifications.

It intentionally does **not** contain operational state such as price history,
inventory quantities, reservations, approved claims, or jurisdiction rules.
Those values are managed by normal application/operations workflows and must
not be reset by a deployment.

For existing rows, the bootstrap reconciles seed-owned descriptive metadata but
preserves lifecycle/operations fields such as `active`,
`online_sale_approved`, and specification verification state. For newly created
rows, the manifest's lifecycle values establish the safe initial state.

Run a non-persistent plan first:

```bash
python3 -m app.cli.seed_catalog plan
```

Apply the catalog baseline:

```bash
python3 -m app.cli.seed_catalog apply
```

Both commands use `DACQUA_MIGRATION_DATABASE_URL` when it is configured,
falling back to `DACQUA_DATABASE_URL` for local development. `plan` performs
the same reconciliation in a transaction and rolls it back.

## PT41 SKU transition (October 2026)

The public catalog now defines ten customer-confirmed SKUs in four families.
Each SKU is its own Product record; there are no artificial family-level sellable
products or SKU aliases. Pureline Solo/Duo/Trio represent 1/2/3 Big Blue
cartridge-filter configurations within Harmony. DD15CLEARPTV has **no**
cartridge filters. Origin DD6ROAE has six stages, including its Alkaline Enhancer.
Dimensions, prices, inventory, and product imagery not confirmed for the new
SKUs are intentionally omitted.

Existing REFINE, DD5ROAE, DD15CAT-TTACPTV, DD15CAT-TTACRV, and DD15CATPTV
rows remain in the database unchanged for prior quotes/orders; **do not**
rename these product identifiers. Instead run:

```bash
cd backend
python3 -m app.cli.pt41_catalog_rollout plan
```

Review the plan, database backup, and outstanding orders/quotes before opting
into `apply`. The apply command runs the canonical seed and retires those old
listings in one transaction; it refuses to touch an old product still approved
for online sale. It **does not** delete historical rows or change prices,
financial records, stock, reservation, or order identifiers. Operations users
must separately review any outstanding commercial commitments before
retirement. The normal `seed_catalog apply` command alone does **not** retire
legacy listings; use the explicit PT41 rollout for an existing database.
