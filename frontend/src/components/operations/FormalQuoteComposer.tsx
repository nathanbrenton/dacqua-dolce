import {
  useMemo,
  useState,
} from "react";

import {
  createFormalQuote,
  presentFormalQuote,
  type OperationsFormalQuote,
  type OperationsProduct,
  type OperationsQuote,
} from "../../api/operations";

type DraftLine = {
  key: number;
  productId: string;
  variantId: string;
  quantity: string;
  unitAmount: string;
};

type FormalQuoteComposerProps = {
  quote: OperationsQuote;
  products: OperationsProduct[];
  onChanged: (
    requestId: string,
    formalQuote: OperationsFormalQuote,
  ) => void;
};

function money(amountMinor: number, currency: string): string {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency,
  }).format(amountMinor / 100);
}

function dollarsToMinor(value: string): number | null {
  const cleaned = value.trim();
  if (cleaned === "") {
    return null;
  }
  if (!/^\d+(?:\.\d{1,2})?$/.test(cleaned)) {
    throw new Error("Enter quoted prices as dollars and cents, for example 2499.00.");
  }
  return Math.round(Number(cleaned) * 100);
}

function defaultLine(
  key: number,
  quote: OperationsQuote,
  products: OperationsProduct[],
): DraftLine {
  const product = products.find((candidate) => candidate.id === quote.product_id)
    ?? products[0];
  return {
    key,
    productId: product?.id ?? "",
    variantId: "",
    quantity: "1",
    unitAmount: "",
  };
}

export function FormalQuoteComposer({
  quote,
  products,
  onChanged,
}: FormalQuoteComposerProps) {
  const [nextKey, setNextKey] = useState(2);
  const [lines, setLines] = useState<DraftLine[]>([
    defaultLine(1, quote, products),
  ]);
  const [customerNote, setCustomerNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const history = useMemo(
    () => [...quote.formal_quotes].sort(
      (left, right) => right.revision_number - left.revision_number,
    ),
    [quote.formal_quotes],
  );
  const latest = history[0] ?? null;
  const approved = history.find((formalQuote) => formalQuote.status === "approved") ?? null;

  function updateLine(
    key: number,
    patch: Partial<DraftLine>,
  ): void {
    setLines((current) => current.map((line) => (
      line.key === key ? { ...line, ...patch } : line
    )));
  }

  async function createDraft(): Promise<void> {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const items = lines.map((line) => {
        if (line.productId === "") {
          throw new Error("Choose a product for every quote line.");
        }
        const quantity = Number.parseInt(line.quantity, 10);
        if (!Number.isInteger(quantity) || quantity < 1) {
          throw new Error("Every quote line needs a quantity of at least 1.");
        }
        return {
          product_id: line.productId,
          variant_id: line.variantId || null,
          quantity,
          unit_amount_minor: dollarsToMinor(line.unitAmount),
        };
      });
      const formalQuote = await createFormalQuote(quote.id, {
        items,
        customer_note: customerNote.trim() || null,
      });
      onChanged(quote.id, formalQuote);
      setNotice(`Draft quote revision ${formalQuote.revision_number} created.`);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Formal quote could not be created.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function presentDraft(formalQuote: OperationsFormalQuote): Promise<void> {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await presentFormalQuote(formalQuote.id);
      onChanged(quote.id, updated);
      setNotice(`Revision ${updated.revision_number} is ready for customer approval.`);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Formal quote could not be presented.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="operations-formal-quote">
      <div className="operations-request-region-heading">
        <p className="operations-request-region-label">Formal quote</p>
        <span>Revisioned commercial snapshot</span>
      </div>

      {history.length > 0 ? (
        <div className="operations-formal-quote-history">
          {history.map((formalQuote) => (
            <article key={formalQuote.id} className="operations-formal-quote-summary">
              <div>
                <strong>Revision {formalQuote.revision_number}</strong>
                <span>{formalQuote.status.replaceAll("_", " ")}</span>
              </div>
              <strong>
                {money(formalQuote.subtotal_amount_minor, formalQuote.currency)}
              </strong>
              {formalQuote.status === "draft" ? (
                <button
                  type="button"
                  className="operations-action secondary"
                  disabled={busy}
                  onClick={() => {
                    void presentDraft(formalQuote);
                  }}
                >
                  Present to customer
                </button>
              ) : null}
            </article>
          ))}
        </div>
      ) : (
        <p className="operations-request-empty">No formal quote has been prepared yet.</p>
      )}

      {approved !== null ? (
        <p className="operations-formal-quote-approved">
          Customer approved revision {approved.revision_number}. Its commercial snapshot is locked.
        </p>
      ) : (
        <div className="operations-formal-quote-builder">
          <p className="field-helper">
            Current catalog prices are used automatically when available. Leave the price blank to
            use that authoritative amount. Private/no-online-price products require a quoted price.
          </p>

          {lines.map((line, index) => {
            const product = products.find((candidate) => candidate.id === line.productId);
            return (
              <div key={line.key} className="operations-formal-quote-line">
                <label className="operations-field">
                  <span>Product</span>
                  <select
                    value={line.productId}
                    onChange={(event) => {
                      updateLine(line.key, {
                        productId: event.target.value,
                        variantId: "",
                        unitAmount: "",
                      });
                    }}
                  >
                    <option value="">Choose product</option>
                    {products.filter((candidate) => candidate.active).map((candidate) => (
                      <option key={candidate.id} value={candidate.id}>
                        {candidate.sku} — {candidate.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="operations-field">
                  <span>Variant</span>
                  <select
                    value={line.variantId}
                    disabled={!product || product.variants.length === 0}
                    onChange={(event) => {
                      updateLine(line.key, { variantId: event.target.value });
                    }}
                  >
                    <option value="">Base product</option>
                    {product?.variants.map((variant) => (
                      <option key={variant.id} value={variant.id}>
                        {variant.sku} — {variant.display_name}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="operations-field">
                  <span>Qty</span>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={line.quantity}
                    onChange={(event) => {
                      updateLine(line.key, { quantity: event.target.value });
                    }}
                  />
                </label>

                <label className="operations-field">
                  <span>Quoted unit price</span>
                  <input
                    type="text"
                    inputMode="decimal"
                    placeholder={
                      product?.pricing.amount_minor === null
                        ? "Required when no catalog amount"
                        : "Use current catalog price"
                    }
                    value={line.unitAmount}
                    onChange={(event) => {
                      updateLine(line.key, { unitAmount: event.target.value });
                    }}
                  />
                </label>

                {lines.length > 1 ? (
                  <button
                    type="button"
                    className="text-button"
                    onClick={() => {
                      setLines((current) => current.filter((candidate) => candidate.key !== line.key));
                    }}
                  >
                    Remove line {index + 1}
                  </button>
                ) : null}
              </div>
            );
          })}

          <button
            type="button"
            className="text-button"
            onClick={() => {
              setLines((current) => [
                ...current,
                defaultLine(nextKey, quote, products),
              ]);
              setNextKey((current) => current + 1);
            }}
          >
            + Add quote line
          </button>

          <label className="operations-field">
            <span>Customer-facing note</span>
            <textarea
              rows={3}
              maxLength={4000}
              placeholder="Optional context that the customer should see with this quote"
              value={customerNote}
              onChange={(event) => {
                setCustomerNote(event.target.value);
              }}
            />
          </label>

          <button
            type="button"
            className="operations-action"
            disabled={busy || lines.length === 0}
            onClick={() => {
              void createDraft();
            }}
          >
            {busy ? "Working…" : "Create Formal Quote Draft"}
          </button>
        </div>
      )}

      {notice !== null ? <p className="operations-save-notice">{notice}</p> : null}
      {error !== null ? <p className="operations-error">{error}</p> : null}
    </section>
  );
}
