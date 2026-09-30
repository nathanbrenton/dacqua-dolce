import {
  useMemo,
  useState,
} from "react";

import type {
  CommercialAddress,
  CommercialChargeKind,
} from "../../api/commercial";
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

type DraftCharge = {
  key: number;
  kind: CommercialChargeKind;
  label: string;
  amount: string;
};

type FormalQuoteComposerProps = {
  quote: OperationsQuote;
  products: OperationsProduct[];
  onChanged: (
    requestId: string,
    formalQuote: OperationsFormalQuote,
  ) => void;
};

const CHARGE_OPTIONS: Array<{
  value: CommercialChargeKind;
  label: string;
  credit: boolean;
}> = [
  { value: "shipping", label: "Shipping / delivery", credit: false },
  { value: "tax", label: "Tax", credit: false },
  { value: "installation", label: "Installation", credit: false },
  { value: "discount", label: "Discount", credit: true },
  { value: "other_charge", label: "Other charge", credit: false },
  { value: "other_credit", label: "Other credit", credit: true },
];

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
    throw new Error("Enter amounts as dollars and cents, for example 2499.00.");
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

function servicePostalCode(quote: OperationsQuote): string {
  const value = quote.recommendation_context?.service_postal_code;
  return typeof value === "string" ? value : "";
}

function defaultAddress(quote: OperationsQuote): CommercialAddress {
  return {
    recipient_name: quote.name,
    line1: "",
    line2: null,
    city: "",
    region_code: "CA",
    postal_code: servicePostalCode(quote),
    country_code: "US",
    phone: quote.phone,
  };
}

function cleanAddress(address: CommercialAddress): CommercialAddress {
  const required = [
    address.recipient_name,
    address.line1,
    address.city,
    address.region_code,
    address.postal_code,
    address.country_code,
  ];
  if (required.some((value) => value.trim() === "")) {
    throw new Error("Complete every required delivery and billing address field.");
  }
  return {
    recipient_name: address.recipient_name.trim(),
    line1: address.line1.trim(),
    line2: address.line2?.trim() || null,
    city: address.city.trim(),
    region_code: address.region_code.trim(),
    postal_code: address.postal_code.trim(),
    country_code: address.country_code.trim().toUpperCase(),
    phone: address.phone?.trim() || null,
  };
}

function AddressFields({
  title,
  value,
  onChange,
}: {
  title: string;
  value: CommercialAddress;
  onChange: (next: CommercialAddress) => void;
}) {
  function update(patch: Partial<CommercialAddress>): void {
    onChange({ ...value, ...patch });
  }

  return (
    <fieldset className="operations-commercial-address">
      <legend>{title}</legend>
      <div className="operations-commercial-address-grid">
        <label className="operations-field">
          <span>Recipient</span>
          <input
            value={value.recipient_name}
            onChange={(event) => update({ recipient_name: event.target.value })}
          />
        </label>
        <label className="operations-field">
          <span>Phone</span>
          <input
            value={value.phone ?? ""}
            onChange={(event) => update({ phone: event.target.value || null })}
          />
        </label>
        <label className="operations-field operations-commercial-address-wide">
          <span>Address line 1</span>
          <input
            value={value.line1}
            onChange={(event) => update({ line1: event.target.value })}
          />
        </label>
        <label className="operations-field operations-commercial-address-wide">
          <span>Address line 2</span>
          <input
            value={value.line2 ?? ""}
            onChange={(event) => update({ line2: event.target.value || null })}
          />
        </label>
        <label className="operations-field">
          <span>City</span>
          <input
            value={value.city}
            onChange={(event) => update({ city: event.target.value })}
          />
        </label>
        <label className="operations-field">
          <span>State / region</span>
          <input
            value={value.region_code}
            onChange={(event) => update({ region_code: event.target.value })}
          />
        </label>
        <label className="operations-field">
          <span>Postal code</span>
          <input
            value={value.postal_code}
            onChange={(event) => update({ postal_code: event.target.value })}
          />
        </label>
        <label className="operations-field">
          <span>Country</span>
          <input
            maxLength={2}
            value={value.country_code}
            onChange={(event) => update({ country_code: event.target.value })}
          />
        </label>
      </div>
    </fieldset>
  );
}

export function FormalQuoteComposer({
  quote,
  products,
  onChanged,
}: FormalQuoteComposerProps) {
  const [nextLineKey, setNextLineKey] = useState(2);
  const [nextChargeKey, setNextChargeKey] = useState(1);
  const [lines, setLines] = useState<DraftLine[]>([
    defaultLine(1, quote, products),
  ]);
  const [charges, setCharges] = useState<DraftCharge[]>([]);
  const [deliveryAddress, setDeliveryAddress] = useState<CommercialAddress>(
    defaultAddress(quote),
  );
  const [billingSame, setBillingSame] = useState(true);
  const [billingAddress, setBillingAddress] = useState<CommercialAddress>(
    defaultAddress(quote),
  );
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
  const approved = history.find((formalQuote) => formalQuote.status === "approved") ?? null;

  function updateLine(
    key: number,
    patch: Partial<DraftLine>,
  ): void {
    setLines((current) => current.map((line) => (
      line.key === key ? { ...line, ...patch } : line
    )));
  }

  function updateCharge(
    key: number,
    patch: Partial<DraftCharge>,
  ): void {
    setCharges((current) => current.map((charge) => (
      charge.key === key ? { ...charge, ...patch } : charge
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

      const commercialCharges = charges.map((charge) => {
        const amount = dollarsToMinor(charge.amount);
        if (amount === null || amount <= 0) {
          throw new Error("Every commercial adjustment needs a positive entered amount.");
        }
        const option = CHARGE_OPTIONS.find((candidate) => candidate.value === charge.kind);
        if (charge.label.trim() === "") {
          throw new Error("Every commercial adjustment needs a customer-facing label.");
        }
        return {
          kind: charge.kind,
          label: charge.label.trim(),
          amount_minor: option?.credit ? -amount : amount,
        };
      });

      const cleanedDelivery = cleanAddress(deliveryAddress);
      const cleanedBilling = billingSame
        ? cleanedDelivery
        : cleanAddress(billingAddress);

      const formalQuote = await createFormalQuote(quote.id, {
        items,
        charges: commercialCharges,
        delivery_address: cleanedDelivery,
        billing_address: cleanedBilling,
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
              <div className="operations-commercial-breakdown">
                <span>
                  Products {money(formalQuote.subtotal_amount_minor, formalQuote.currency)}
                </span>
                {formalQuote.charges.map((charge, index) => (
                  <span key={`${formalQuote.id}-${charge.kind}-${index}`}>
                    {charge.label} {money(charge.amount_minor, formalQuote.currency)}
                  </span>
                ))}
                <strong>
                  Final total {money(formalQuote.total_amount_minor, formalQuote.currency)}
                </strong>
              </div>
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
            Shipping, tax, installation, discounts, and other adjustments are entered explicitly;
            this workflow does not calculate them automatically.
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
                defaultLine(nextLineKey, quote, products),
              ]);
              setNextLineKey((current) => current + 1);
            }}
          >
            + Add quote line
          </button>

          <div className="operations-commercial-adjustments">
            <div className="operations-request-region-heading">
              <p className="operations-request-region-label">Commercial adjustments</p>
              <span>Manual, explicit amounts only</span>
            </div>
            {charges.map((charge) => (
              <div key={charge.key} className="operations-commercial-charge-row">
                <label className="operations-field">
                  <span>Type</span>
                  <select
                    value={charge.kind}
                    onChange={(event) => {
                      updateCharge(charge.key, {
                        kind: event.target.value as CommercialChargeKind,
                      });
                    }}
                  >
                    {CHARGE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="operations-field">
                  <span>Customer-facing label</span>
                  <input
                    value={charge.label}
                    onChange={(event) => updateCharge(charge.key, { label: event.target.value })}
                  />
                </label>
                <label className="operations-field">
                  <span>Amount</span>
                  <input
                    inputMode="decimal"
                    placeholder="0.00"
                    value={charge.amount}
                    onChange={(event) => updateCharge(charge.key, { amount: event.target.value })}
                  />
                </label>
                <button
                  type="button"
                  className="text-button"
                  onClick={() => {
                    setCharges((current) => current.filter((candidate) => candidate.key !== charge.key));
                  }}
                >
                  Remove
                </button>
              </div>
            ))}
            <button
              type="button"
              className="text-button"
              onClick={() => {
                const key = nextChargeKey;
                setCharges((current) => [
                  ...current,
                  {
                    key,
                    kind: "shipping",
                    label: "Shipping / delivery",
                    amount: "",
                  },
                ]);
                setNextChargeKey((current) => current + 1);
              }}
            >
              + Add commercial adjustment
            </button>
          </div>

          <AddressFields
            title="Delivery / service address snapshot"
            value={deliveryAddress}
            onChange={setDeliveryAddress}
          />

          <label className="operations-checkbox-row">
            <input
              type="checkbox"
              checked={billingSame}
              onChange={(event) => setBillingSame(event.target.checked)}
            />
            <span>Billing address is the same as delivery / service address</span>
          </label>

          {!billingSame ? (
            <AddressFields
              title="Billing address snapshot"
              value={billingAddress}
              onChange={setBillingAddress}
            />
          ) : null}

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

          <p className="field-helper">
            Deposits / partial-payment schedules are intentionally not represented yet. The final
            quote total remains the amount the hosted payment flow must collect in full.
          </p>

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
