import {
  type ChangeEvent,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getOperationsCatalog,
  getOperationsQuotes,
  getOperationsSummary,
  updateProductInventory,
  updateProductPricing,
  updateQuoteNotes,
  updateQuoteStatus,
  type OperationsProduct,
  type OperationsQuote,
  type OperationsSummary,
} from "../../api/operations";

type OperationsPageProps = {
  roles: string[];
  onNavigate: (path: string) => void;
};

const OPERATIONS_ROLES = new Set([
  "employee",
  "manager",
  "administrator",
  "developer",
]);

const PRIVILEGED_ROLES = new Set([
  "manager",
  "administrator",
  "developer",
]);

const QUOTE_STATUSES = [
  "new",
  "contacted",
  "quoted",
  "closed",
] as const;

const PRICING_MODES = [
  "PUBLIC",
  "MAP_LIMITED",
  "CART_ONLY",
  "PRIVATE_QUOTE",
  "LOGIN_REQUIRED",
  "NO_ONLINE_PRICE",
  "NO_ONLINE_SALE",
] as const;

const AMOUNT_REQUIRED = new Set<string>([
  "PUBLIC",
  "MAP_LIMITED",
  "CART_ONLY",
  "LOGIN_REQUIRED",
]);

const INVENTORY_STATUSES = [
  "in_stock",
  "low_stock",
  "backordered",
  "unavailable",
  "not_tracked",
] as const;

type PricingDraft = {
  mode: string;
  amount: string;
  currency: string;
};

type InventoryDraft = {
  status: string;
  quantityOnHand: string;
  quantityReserved: string;
};

type SaveState =
  | "idle"
  | "saving"
  | "saved";

function dollarsToMinor(value: string): number | null {
  const normalized = value.trim();

  if (normalized.length === 0) {
    return null;
  }

  if (!/^\d+(\.\d{1,2})?$/.test(normalized)) {
    throw new Error(
      "Enter a dollar amount with no more than two decimals.",
    );
  }

  const amount = Number(normalized);

  if (!Number.isFinite(amount)) {
    throw new Error("Enter a valid amount.");
  }

  return Math.round(amount * 100);
}

function minorToDollars(amountMinor: number | null): string {
  if (amountMinor === null) {
    return "";
  }

  return (amountMinor / 100).toFixed(2);
}

function replaceProduct(
  products: OperationsProduct[],
  replacement: OperationsProduct,
): OperationsProduct[] {
  return products.map((product) =>
    product.id === replacement.id ? replacement : product,
  );
}

export function OperationsPage({
  roles,
  onNavigate,
}: OperationsPageProps) {
  const authorized = useMemo(
    () => roles.some((role) => OPERATIONS_ROLES.has(role)),
    [roles],
  );

  const privileged = useMemo(
    () => roles.some((role) => PRIVILEGED_ROLES.has(role)),
    [roles],
  );

  const [summary, setSummary] =
    useState<OperationsSummary | null>(null);
  const [quotes, setQuotes] =
    useState<OperationsQuote[]>([]);
  const [products, setProducts] =
    useState<OperationsProduct[]>([]);
  const [pricingDrafts, setPricingDrafts] =
    useState<Record<string, PricingDraft>>({});
  const [inventoryDrafts, setInventoryDrafts] =
    useState<Record<string, InventoryDraft>>({});
  const [quoteNoteDrafts, setQuoteNoteDrafts] =
    useState<Record<string, string>>({});
  const [error, setError] =
    useState<string | null>(null);
  const [message, setMessage] =
    useState<string | null>(null);
  const [loading, setLoading] =
    useState(true);
  const [
    pricingSaveStates,
    setPricingSaveStates,
  ] = useState<Record<string, SaveState>>({});
  const [
    inventorySaveStates,
    setInventorySaveStates,
  ] = useState<Record<string, SaveState>>({});
  const [
    quoteNoteSaveStates,
    setQuoteNoteSaveStates,
  ] = useState<Record<string, SaveState>>({});

  useEffect(() => {
    if (!authorized) {
      setLoading(false);
      return;
    }

    void Promise.all([
      getOperationsSummary(),
      getOperationsQuotes(),
      getOperationsCatalog(),
    ])
      .then(([summaryResult, quoteResult, productResult]) => {
        setSummary(summaryResult);
        setQuotes(quoteResult);
        setProducts(productResult);

        const nextQuoteNotes: Record<string, string> = {};

        for (const quote of quoteResult) {
          nextQuoteNotes[quote.id] =
            quote.internal_notes ?? "";
        }

        setQuoteNoteDrafts(nextQuoteNotes);

        const nextPricing: Record<string, PricingDraft> = {};
        const nextInventory: Record<string, InventoryDraft> = {};

        for (const product of productResult) {
          nextPricing[product.id] = {
            mode: product.pricing.mode,
            amount: minorToDollars(product.pricing.amount_minor),
            currency: product.pricing.currency ?? "USD",
          };

          nextInventory[product.id] = {
            status: product.inventory.status,
            quantityOnHand: String(product.inventory.quantity_on_hand),
            quantityReserved: String(product.inventory.quantity_reserved),
          };
        }

        setPricingDrafts(nextPricing);
        setInventoryDrafts(nextInventory);
        setError(null);
      })
      .catch((caught) => {
        setError(
          caught instanceof Error
            ? caught.message
            : "Operations data could not be loaded.",
        );
      })
      .finally(() => {
        setLoading(false);
      });
  }, [authorized]);

  if (!authorized) {
    return (
      <main className="operations-shell">
        <button
          type="button"
          className="text-button"
          onClick={() => onNavigate("/")}
        >
          ← Home
        </button>

        <section className="operations-denied">
          <p className="eyebrow">Operations</p>
          <h1>Access restricted.</h1>
          <p>
            This workspace is limited to authorized operations roles.
          </p>
        </section>
      </main>
    );
  }

  async function saveQuoteStatus(
    quote: OperationsQuote,
    nextStatus: string,
  ) {
    setError(null);
    setMessage(null);

    try {
      const updated = await updateQuoteStatus(
        quote.id,
        nextStatus,
      );

      setQuotes((current) =>
        current.map((candidate) =>
          candidate.id === updated.id ? updated : candidate,
        ),
      );

      setSummary(await getOperationsSummary());
      setMessage("Quote status updated.");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Quote status update failed.",
      );
    }
  }

  async function saveQuoteNotes(
    quote: OperationsQuote,
  ) {
    const draft =
      quoteNoteDrafts[quote.id];

    if (draft === undefined) {
      return;
    }

    setError(null);
    setMessage(null);
    setQuoteNoteSaveStates((current) => ({
      ...current,
      [quote.id]: "saving",
    }));

    try {
      const normalized =
        draft.trim().length > 0
          ? draft
          : null;

      const updated =
        await updateQuoteNotes(
          quote.id,
          normalized,
        );

      setQuotes((current) =>
        current.map((candidate) =>
          candidate.id === updated.id
            ? updated
            : candidate,
        ),
      );

      setQuoteNoteDrafts((current) => ({
        ...current,
        [quote.id]:
          updated.internal_notes ?? "",
      }));

      setQuoteNoteSaveStates((current) => ({
        ...current,
        [quote.id]: "saved",
      }));

      setMessage(
        "Internal quote notes saved.",
      );

      window.setTimeout(() => {
        setQuoteNoteSaveStates((current) => ({
          ...current,
          [quote.id]: "idle",
        }));
      }, 1800);
    } catch (caught) {
      setQuoteNoteSaveStates((current) => ({
        ...current,
        [quote.id]: "idle",
      }));

      setError(
        caught instanceof Error
          ? caught.message
          : "Internal quote notes could not be saved.",
      );
    }
  }

  async function savePricing(product: OperationsProduct) {
    const draft = pricingDrafts[product.id];

    if (draft === undefined) {
      return;
    }

    setError(null);
    setMessage(null);
    setPricingSaveStates((current) => ({
      ...current,
      [product.id]: "saving",
    }));

    try {
      const amountMinor = AMOUNT_REQUIRED.has(draft.mode)
        ? dollarsToMinor(draft.amount)
        : null;

      if (
        AMOUNT_REQUIRED.has(draft.mode)
        && amountMinor === null
      ) {
        throw new Error("This pricing policy requires an amount.");
      }

      const updated = await updateProductPricing(product.id, {
        mode: draft.mode,
        amount_minor: amountMinor,
        currency: draft.currency,
      });

      setProducts((current) => replaceProduct(current, updated));
      setPricingDrafts((current) => ({
        ...current,
        [updated.id]: {
          mode: updated.pricing.mode,
          amount: minorToDollars(updated.pricing.amount_minor),
          currency: updated.pricing.currency ?? "USD",
        },
      }));
      setMessage(`Pricing policy saved for ${updated.sku}.`);
      setPricingSaveStates((current) => ({
        ...current,
        [product.id]: "saved",
      }));

      window.setTimeout(() => {
        setPricingSaveStates((current) => ({
          ...current,
          [product.id]: "idle",
        }));
      }, 1800);
    } catch (caught) {
      setPricingSaveStates((current) => ({
        ...current,
        [product.id]: "idle",
      }));
      setError(
        caught instanceof Error
          ? caught.message
          : "Pricing update failed.",
      );
    }
  }

  async function saveInventory(product: OperationsProduct) {
    const draft = inventoryDrafts[product.id];

    if (draft === undefined) {
      return;
    }

    setError(null);
    setMessage(null);

    const quantityOnHand = Number.parseInt(draft.quantityOnHand, 10);
    const quantityReserved = Number.parseInt(
      draft.quantityReserved,
      10,
    );

    if (
      !Number.isInteger(quantityOnHand)
      || quantityOnHand < 0
      || !Number.isInteger(quantityReserved)
      || quantityReserved < 0
    ) {
      setError("Inventory quantities must be non-negative integers.");
      return;
    }

    setInventorySaveStates((current) => ({
      ...current,
      [product.id]: "saving",
    }));

    try {
      const updated = await updateProductInventory(product.id, {
        status: draft.status,
        quantity_on_hand: quantityOnHand,
        quantity_reserved: quantityReserved,
      });

      setProducts((current) => replaceProduct(current, updated));
      setInventoryDrafts((current) => ({
        ...current,
        [updated.id]: {
          status: updated.inventory.status,
          quantityOnHand: String(updated.inventory.quantity_on_hand),
          quantityReserved: String(updated.inventory.quantity_reserved),
        },
      }));
      setMessage(`Inventory saved for ${updated.sku}.`);
      setInventorySaveStates((current) => ({
        ...current,
        [product.id]: "saved",
      }));

      window.setTimeout(() => {
        setInventorySaveStates((current) => ({
          ...current,
          [product.id]: "idle",
        }));
      }, 1800);
    } catch (caught) {
      setInventorySaveStates((current) => ({
        ...current,
        [product.id]: "idle",
      }));
      setError(
        caught instanceof Error
          ? caught.message
          : "Inventory update failed.",
      );
    }
  }

  function updatePricingDraft(
    productId: string,
    field: keyof PricingDraft,
    value: string,
  ) {
    setPricingDrafts((current) => {
      const existing = current[productId];

      if (existing === undefined) {
        return current;
      }

      return {
        ...current,
        [productId]: {
          ...existing,
          [field]: value,
        },
      };
    });
  }

  function updateInventoryDraft(
    productId: string,
    field: keyof InventoryDraft,
    value: string,
  ) {
    setInventoryDrafts((current) => {
      const existing = current[productId];

      if (existing === undefined) {
        return current;
      }

      return {
        ...current,
        [productId]: {
          ...existing,
          [field]: value,
        },
      };
    });
  }

  const nextAction = (
    summary === null
      ? null
      : summary.new_quotes > 0
        ? {
            title: "Review new quote requests",
            detail:
              `${summary.new_quotes} new customer `
              + (
                summary.new_quotes === 1
                  ? "request needs"
                  : "requests need"
              )
              + " attention.",
            href: "#quote-queue",
          }
        : summary.failed_email_deliveries > 0
          ? {
              title: "Investigate email delivery",
              detail:
                `${summary.failed_email_deliveries} failed email `
                + (
                  summary.failed_email_deliveries === 1
                    ? "delivery requires"
                    : "deliveries require"
                )
                + " review.",
              href: null,
            }
          : summary.open_quotes > 0
            ? {
                title: "Continue open quotes",
                detail:
                  `${summary.open_quotes} open quote `
                  + (
                    summary.open_quotes === 1
                      ? "request remains"
                      : "requests remain"
                  )
                  + " in the queue.",
                href: "#quote-queue",
              }
            : {
                title: "No urgent actions",
                detail:
                  "The current operations queues "
                  + "do not show an urgent item.",
                href: null,
              }
  );

  return (
    <main className="operations-shell">
      <button
        type="button"
        className="text-button"
        onClick={() => onNavigate("/")}
      >
        ← Customer site
      </button>

      <header className="operations-heading">
        <p className="eyebrow">Operations</p>
        <h1>Business control, without business rules in the browser.</h1>
        <p>
          Pricing, inventory, and quote state are authoritative
          server-side records with role enforcement and audit events.
        </p>
      </header>

      {error !== null ? (
        <p className="operations-alert operations-error" role="alert">
          {error}
        </p>
      ) : null}

      {message !== null ? (
        <p className="operations-alert" role="status">
          {message}
        </p>
      ) : null}

      {loading ? <p role="status">Loading operations…</p> : null}

      {summary !== null ? (
        <section
          className="operations-metrics"
          aria-label="Operations summary"
        >
          <article>
            <strong>{summary.new_quotes}</strong>
            <span>New quotes</span>
          </article>
          <article>
            <strong>{summary.open_quotes}</strong>
            <span>Open quotes</span>
          </article>
          <article>
            <strong>{summary.active_products}</strong>
            <span>Active systems</span>
          </article>
          <article>
            <strong>{summary.failed_email_deliveries}</strong>
            <span>Email failures</span>
          </article>
        </section>
      ) : null}

      {nextAction !== null ? (
        <section
          className="operations-next-action"
          aria-labelledby="operations-next-action-title"
        >
          <span>Next action</span>

          <div>
            <strong id="operations-next-action-title">
              {nextAction.title}
            </strong>
            <p>{nextAction.detail}</p>
          </div>

          {nextAction.href !== null ? (
            <a href={nextAction.href}>
              Open queue
            </a>
          ) : null}
        </section>
      ) : null}

      <section
        id="quote-queue"
        className="operations-section"
      >
        <div className="operations-section-heading">
          <p className="eyebrow">Quote Queue</p>
          <h2>Customer requests</h2>
        </div>

        {quotes.length === 0 ? (
          <p className="account-muted">No quote requests.</p>
        ) : (
          <div className="operations-quote-list">
            {quotes.map((quote) => (
              <article key={quote.id} className="operations-quote">
                <div className="operations-quote-main">
                  <p className="product-meta">
                    {quote.product_name ?? "General consultation"}
                  </p>
                  <h3>{quote.name}</h3>
                  <p>
                    <a href={`mailto:${quote.email}`}>{quote.email}</a>
                    {quote.phone !== null ? (
                      <>
                        {" · "}
                        <a href={`tel:${quote.phone}`}>{quote.phone}</a>
                      </>
                    ) : null}
                  </p>
                  {quote.message !== null ? (
                    <p className="operations-customer-message">
                      {quote.message}
                    </p>
                  ) : null}

                  <label className="operations-field">
                    <span>Internal notes</span>
                    <textarea
                      rows={3}
                      maxLength={8000}
                      placeholder="Private operations notes"
                      value={
                        quoteNoteDrafts[quote.id]
                        ?? ""
                      }
                      onChange={(event) => {
                        setQuoteNoteDrafts(
                          (current) => ({
                            ...current,
                            [quote.id]:
                              event.target.value,
                          }),
                        );
                      }}
                    />
                  </label>

                  <small className="operations-note">
                    Private — never shown to the customer.
                  </small>

                  <button
                    type="button"
                    className={
                      "operations-action secondary "
                      + (
                        (
                          quoteNoteSaveStates[quote.id]
                          ?? "idle"
                        ) === "saved"
                          ? "is-saved"
                          : ""
                      )
                    }
                    disabled={
                      (
                        quoteNoteSaveStates[quote.id]
                        ?? "idle"
                      ) === "saving"
                    }
                    onClick={() => {
                      void saveQuoteNotes(quote);
                    }}
                  >
                    {(
                      quoteNoteSaveStates[quote.id]
                      ?? "idle"
                    ) === "saving"
                      ? "Saving…"
                      : (
                          quoteNoteSaveStates[quote.id]
                          ?? "idle"
                        ) === "saved"
                        ? "Saved ✓"
                        : "Save Internal Notes"}
                  </button>

                  <small>
                    {new Date(quote.created_at).toLocaleString()}
                  </small>
                </div>

                <label className="operations-field">
                  <span>Status</span>
                  <select
                    value={quote.status}
                    onChange={(event: ChangeEvent<HTMLSelectElement>) => {
                      void saveQuoteStatus(quote, event.target.value);
                    }}
                  >
                    {QUOTE_STATUSES.map((quoteStatus) => (
                      <option key={quoteStatus} value={quoteStatus}>
                        {quoteStatus}
                      </option>
                    ))}
                  </select>
                </label>
              </article>
            ))}
          </div>
        )}
      </section>

      <section
        id="catalog-governance"
        className="operations-section"
      >
        <div className="operations-section-heading">
          <p className="eyebrow">Catalog Governance</p>
          <h2>Pricing &amp; inventory</h2>
          <p>
            Enter only authoritative business/manufacturer data.
            Restricted products should use a non-public pricing policy
            rather than a workaround.
          </p>
        </div>

        <div className="operations-product-list">
          {products.map((product) => {
            const pricing = pricingDrafts[product.id];
            const inventory = inventoryDrafts[product.id];

            if (pricing === undefined || inventory === undefined) {
              return null;
            }

            const amountNeeded = AMOUNT_REQUIRED.has(pricing.mode);
            const pricingSaveState =
              pricingSaveStates[product.id]
              ?? "idle";
            const inventorySaveState =
              inventorySaveStates[product.id]
              ?? "idle";

            return (
              <article key={product.id} className="operations-product">
                <header>
                  <p className="product-meta">
                    {product.manufacturer}
                    {" · "}
                    {product.category}
                  </p>
                  <h3>{product.name}</h3>
                  <code>{product.sku}</code>
                </header>

                <div className="operations-product-grid">
                  <fieldset>
                    <legend>Pricing policy</legend>

                    <label className="operations-field">
                      <span>Mode</span>
                      <select
                        value={pricing.mode}
                        disabled={!privileged}
                        onChange={(event: ChangeEvent<HTMLSelectElement>) => {
                          updatePricingDraft(
                            product.id,
                            "mode",
                            event.target.value,
                          );
                        }}
                      >
                        {PRICING_MODES.map((mode) => (
                          <option key={mode} value={mode}>
                            {mode}
                          </option>
                        ))}
                      </select>
                    </label>

                    <div className="operations-field-row">
                      <label className="operations-field">
                        <span>Amount</span>
                        <input
                          inputMode="decimal"
                          placeholder={amountNeeded ? "0.00" : "Hidden"}
                          value={amountNeeded ? pricing.amount : ""}
                          disabled={!privileged || !amountNeeded}
                          onChange={(event: ChangeEvent<HTMLInputElement>) => {
                            updatePricingDraft(
                              product.id,
                              "amount",
                              event.target.value,
                            );
                          }}
                        />
                      </label>

                      <label className="operations-field">
                        <span>Currency</span>
                        <input
                          maxLength={3}
                          value={pricing.currency}
                          disabled={!privileged}
                          onChange={(event: ChangeEvent<HTMLInputElement>) => {
                            updatePricingDraft(
                              product.id,
                              "currency",
                              event.target.value.toUpperCase(),
                            );
                          }}
                        />
                      </label>
                    </div>

                    <button
                      type="button"
                      className={
                        "operations-action "
                        + (
                          pricingSaveState === "saved"
                            ? "is-saved"
                            : ""
                        )
                      }
                      disabled={
                        !privileged
                        || pricingSaveState === "saving"
                      }
                      onClick={() => void savePricing(product)}
                    >
                      {pricingSaveState === "saving"
                        ? "Saving…"
                        : pricingSaveState === "saved"
                          ? "Saved ✓"
                          : "Save Pricing Policy"}
                    </button>

                    {!privileged ? (
                      <p className="operations-note">
                        Manager, administrator, or developer role required
                        to change pricing.
                      </p>
                    ) : null}
                  </fieldset>

                  <fieldset>
                    <legend>Inventory</legend>

                    <label className="operations-field">
                      <span>Status</span>
                      <select
                        value={inventory.status}
                        onChange={(event: ChangeEvent<HTMLSelectElement>) => {
                          updateInventoryDraft(
                            product.id,
                            "status",
                            event.target.value,
                          );
                        }}
                      >
                        {INVENTORY_STATUSES.map((inventoryStatus) => (
                          <option
                            key={inventoryStatus}
                            value={inventoryStatus}
                          >
                            {inventoryStatus}
                          </option>
                        ))}
                      </select>
                    </label>

                    <div className="operations-field-row">
                      <label className="operations-field">
                        <span>On hand</span>
                        <input
                          type="number"
                          min={0}
                          step={1}
                          value={inventory.quantityOnHand}
                          onChange={(event: ChangeEvent<HTMLInputElement>) => {
                            updateInventoryDraft(
                              product.id,
                              "quantityOnHand",
                              event.target.value,
                            );
                          }}
                        />
                      </label>

                      <label className="operations-field">
                        <span>Reserved</span>
                        <input
                          type="number"
                          min={0}
                          step={1}
                          value={inventory.quantityReserved}
                          onChange={(event: ChangeEvent<HTMLInputElement>) => {
                            updateInventoryDraft(
                              product.id,
                              "quantityReserved",
                              event.target.value,
                            );
                          }}
                        />
                      </label>
                    </div>

                    <button
                      type="button"
                      className={
                        "operations-action secondary "
                        + (
                          inventorySaveState === "saved"
                            ? "is-saved"
                            : ""
                        )
                      }
                      disabled={
                        inventorySaveState === "saving"
                      }
                      onClick={() => void saveInventory(product)}
                    >
                      {inventorySaveState === "saving"
                        ? "Saving…"
                        : inventorySaveState === "saved"
                          ? "Saved ✓"
                          : "Save Inventory"}
                    </button>
                  </fieldset>
                </div>
              </article>
            );
          })}
        </div>
      </section>
    </main>
  );
}
