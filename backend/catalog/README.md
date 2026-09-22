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
