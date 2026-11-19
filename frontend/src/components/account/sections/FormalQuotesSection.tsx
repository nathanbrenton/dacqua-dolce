// Formal quotes presented to the customer: line items, policies to
// acknowledge, the shipping-insurance choice, and approval (which prepares an
// order, so the order list is refreshed afterwards).
//
// API: recordShippingInsuranceDecision, approveCustomerFormalQuote in
//   api/account.ts -> /api/account/quotes/{id}/...; getOrders in api/orders.ts

import {
  type Dispatch,
  type SetStateAction,
  useState,
} from "react";
import {
  approveCustomerFormalQuote,
  type CustomerFormalQuote,
  recordShippingInsuranceDecision,
} from "../../../api/account";
import { getOrders, type Order } from "../../../api/orders";
import { type SalesArea, salesAreaAllowsAddress } from "../../../api/salesArea";
import {
  commercialAddressLines,
  formalQuoteExpired,
  money,
} from "../accountFormat";
import { type AccountNoticeProps } from "../accountShared";

type FormalQuotesSectionProps = {
  formalQuotes: CustomerFormalQuote[];
  onFormalQuotesChange: Dispatch<SetStateAction<CustomerFormalQuote[]>>;
  orders: Order[];
  onOrdersChange: (orders: Order[]) => void;
  salesArea: SalesArea | null;
} & AccountNoticeProps;

export function FormalQuotesSection({
  formalQuotes,
  onFormalQuotesChange: setFormalQuotes,
  orders,
  onOrdersChange: setOrders,
  salesArea,
  onError: setError,
  onNotice: setSaveNotice,
}: FormalQuotesSectionProps) {
  const [policyAcknowledgments, setPolicyAcknowledgments] =
    useState<Record<string, boolean>>({});
  const [insuranceDecisionBusyQuoteId, setInsuranceDecisionBusyQuoteId] =
    useState<string | null>(null);

  async function setShippingInsuranceDecision(
    quote: CustomerFormalQuote,
    decision: "accepted" | "declined",
  ): Promise<void> {
    setError(null);
    setSaveNotice(null);
    setInsuranceDecisionBusyQuoteId(quote.id);
    try {
      const updated = await recordShippingInsuranceDecision(
        quote.id,
        decision,
      );
      setFormalQuotes((current) => current.map((candidate) => (
        candidate.id === updated.id ? updated : candidate
      )));
      setSaveNotice(
        decision === "accepted"
          ? "Shipping insurance accepted for this quote revision."
          : "Shipping insurance declined. D’Acqua Dolce can prepare a revised quote without the insurance charge.",
      );
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Shipping insurance choice could not be recorded.",
      );
    } finally {
      setInsuranceDecisionBusyQuoteId(null);
    }
  }

  async function approveFormalQuote(quote: CustomerFormalQuote): Promise<void> {
    if (policyAcknowledgments[quote.id] !== true) {
      setError("Review and acknowledge the policy versions attached to this quote.");
      return;
    }

    if (
      quote.shipping_insurance_offered
      && quote.shipping_insurance_decision !== "accepted"
    ) {
      setError(
        quote.shipping_insurance_decision === "declined"
          ? "Shipping insurance was declined. Contact D’Acqua Dolce for a revised quote without the insurance charge."
          : "Accept or decline shipping insurance before approving this quote.",
      );
      return;
    }

    const confirmed = window.confirm(
      `Approve quote revision ${quote.revision_number} for ${money(
        quote.total_amount_minor,
        quote.currency,
      )}?`,
    );
    if (!confirmed) {
      return;
    }

    setError(null);
    setSaveNotice(null);
    try {
      const updated = await approveCustomerFormalQuote(
        quote.id,
        quote.policy_snapshots.map((snapshot) => snapshot.id),
      );
      const refreshedOrders = await getOrders();
      setFormalQuotes((current) => current.map((candidate) => (
        candidate.id === updated.id ? updated : candidate
      )));
      setOrders(refreshedOrders);
      setSaveNotice(
        `Quote revision ${updated.revision_number} approved and order prepared.`,
      );
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Quote approval failed.",
      );
    }
  }

  return (
    <section className="account-panel account-formal-quotes-panel">
      <p className="eyebrow">Quotes</p>
      <h2>Review and approve formal quotes.</h2>
      {formalQuotes.length === 0 ? (
        <p className="account-muted">No formal quotes are ready for this account yet.</p>
      ) : (
        <div className="account-formal-quote-list">
          {formalQuotes.map((quote) => (
            <article key={quote.id} className="account-formal-quote">
              <header>
                <div>
                  <strong>Quote revision {quote.revision_number}</strong>
                  <p>{quote.status.replaceAll("_", " ")}</p>
                  {quote.expires_at !== null ? (
                    <small>
                      Valid through {new Date(quote.expires_at).toLocaleDateString()}
                    </small>
                  ) : null}
                </div>
                <strong>{money(quote.total_amount_minor, quote.currency)}</strong>
              </header>

              <div className="account-formal-quote-lines">
                {quote.items.map((item) => (
                  <div key={`${quote.id}-${item.sku}-${item.name}`}>
                    <span>{item.quantity} × {item.name}</span>
                    <strong>{money(item.line_total_minor, item.currency)}</strong>
                    {item.estimated_lead_time !== null ? (
                      <small>Estimated lead time: {item.estimated_lead_time}</small>
                    ) : null}
                  </div>
                ))}
                <div>
                  <span>Product / other costs</span>
                  <strong>
                    {money(
                      quote.cost_breakdown.product_other_amount_minor,
                      quote.currency,
                    )}
                  </strong>
                </div>
                <div>
                  <span>Shipping / delivery</span>
                  <strong>
                    {money(
                      quote.cost_breakdown.shipping_delivery_amount_minor,
                      quote.currency,
                    )}
                  </strong>
                </div>
                <div>
                  <span>Shipping insurance</span>
                  <strong>
                    {money(
                      quote.cost_breakdown.shipping_insurance_amount_minor,
                      quote.currency,
                    )}
                  </strong>
                </div>
                <div>
                  <span>Tax</span>
                  <strong>
                    {money(quote.cost_breakdown.tax_amount_minor, quote.currency)}
                  </strong>
                </div>
                <div>
                  <span>Total cost</span>
                  <strong>
                    {money(quote.cost_breakdown.total_amount_minor, quote.currency)}
                  </strong>
                </div>
                {quote.charges.length > 0 ? (
                  <small className="account-muted">
                    Adjustments: {quote.charges
                      .map(
                        (charge) =>
                          `${charge.label} ${money(charge.amount_minor, quote.currency)}`,
                      )
                      .join(" · ")}
                  </small>
                ) : null}
              </div>

              <div className="account-formal-quote-addresses">
                {quote.delivery_address !== null ? (
                  <div>
                    <strong>Delivery / service address</strong>
                    <address>
                      {commercialAddressLines(quote.delivery_address).map((line) => (
                        <span key={line}>{line}<br /></span>
                      ))}
                    </address>
                    {salesArea?.enforcement_enabled ? (
                      <p className="account-muted">
                        {salesAreaAllowsAddress(
                          salesArea,
                          quote.delivery_address,
                        )
                          ? `Delivery eligible within ${salesArea.label}.`
                          : `This delivery address is outside ${salesArea.label}. Contact D’Acqua Dolce for assistance.`}
                      </p>
                    ) : null}
                  </div>
                ) : null}
                {quote.billing_address !== null ? (
                  <div>
                    <strong>Billing address</strong>
                    <address>
                      {commercialAddressLines(quote.billing_address).map((line) => (
                        <span key={line}>{line}<br /></span>
                      ))}
                    </address>
                  </div>
                ) : null}
              </div>

              {quote.customer_note !== null ? (
                <p className="account-formal-quote-note">{quote.customer_note}</p>
              ) : null}

              {quote.warranty_snapshots.length > 0 ? (
                <div className="account-formal-quote-policies">
                  <strong>Manufacturer warranty documents attached to this quote</strong>
                  {quote.warranty_snapshots.map((snapshot) => (
                    <div key={snapshot.id} className="account-warranty-snapshot">
                      <a href={snapshot.path}>
                        {snapshot.product_name}: {snapshot.title}
                      </a>
                      <small>
                        {snapshot.manufacturer_name} · version {snapshot.version} · verified {new Date(snapshot.verified_at).toLocaleDateString()}
                      </small>
                    </div>
                  ))}
                  <p className="account-muted">
                    D’Acqua Dolce is your primary contact for warranty assistance.
                  </p>
                </div>
              ) : null}

              <div className="account-formal-quote-policies">
                <strong>Policy versions attached to this quote</strong>
                {quote.policy_snapshots.map((snapshot) => (
                  <details key={snapshot.id}>
                    <summary>
                      {snapshot.title} · version {snapshot.version}
                    </summary>
                    <div className="account-policy-snapshot-body">
                      {snapshot.body}
                    </div>
                  </details>
                ))}
              </div>

              {quote.status === "presented" ? (
                <>
                  {quote.shipping_insurance_offered ? (
                    <fieldset className="account-policy-acknowledgment">
                      <legend>Shipping insurance choice</legend>
                      <label>
                        <input
                          type="radio"
                          name={`shipping-insurance-${quote.id}`}
                          value="accepted"
                          checked={quote.shipping_insurance_decision === "accepted"}
                          disabled={insuranceDecisionBusyQuoteId === quote.id}
                          onChange={() => {
                            void setShippingInsuranceDecision(quote, "accepted");
                          }}
                        />
                        <span>
                          Accept shipping insurance for this quote revision.
                        </span>
                      </label>
                      <label>
                        <input
                          type="radio"
                          name={`shipping-insurance-${quote.id}`}
                          value="declined"
                          checked={quote.shipping_insurance_decision === "declined"}
                          disabled={insuranceDecisionBusyQuoteId === quote.id}
                          onChange={() => {
                            void setShippingInsuranceDecision(quote, "declined");
                          }}
                        />
                        <span>
                          Decline shipping insurance for this quote revision.
                        </span>
                      </label>
                      {quote.shipping_insurance_decision === "declined" ? (
                        <small className="account-muted">
                          This quote includes a shipping insurance charge. D’Acqua Dolce must prepare a revised quote without that charge before approval.
                        </small>
                      ) : null}
                    </fieldset>
                  ) : (
                    <p className="account-muted">
                      Shipping insurance is not included in this quote revision.
                    </p>
                  )}
                  <label className="account-policy-acknowledgment">
                    <input
                      type="checkbox"
                      checked={policyAcknowledgments[quote.id] === true}
                      onChange={(event) => {
                        setPolicyAcknowledgments((current) => ({
                          ...current,
                          [quote.id]: event.target.checked,
                        }));
                      }}
                    />
                    <span>
                      I reviewed the policy versions attached to this quote.
                    </span>
                  </label>
                {formalQuoteExpired(quote) ? (
                  <p className="account-muted">
                    This quote has expired. Contact D’Acqua Dolce for a current revision.
                  </p>
                ) : null}
                {salesArea?.enforcement_enabled
                  && !salesAreaAllowsAddress(
                    salesArea,
                    quote.delivery_address,
                  ) ? (
                    <p className="account-muted">
                      This quote cannot be approved for the current delivery address.
                    </p>
                  ) : null}
                <button
                  type="button"
                  className="account-action"
                  disabled={
                    formalQuoteExpired(quote)
                    || (
                      quote.shipping_insurance_offered
                      && quote.shipping_insurance_decision !== "accepted"
                    )
                    || (
                      salesArea?.enforcement_enabled === true
                      && !salesAreaAllowsAddress(
                        salesArea,
                        quote.delivery_address,
                      )
                    )
                  }
                  onClick={() => {
                    void approveFormalQuote(quote);
                  }}
                >
                  {formalQuoteExpired(quote) ? "Quote Expired" : "Approve This Quote"}
                </button>
                </>
              ) : quote.status === "approved" ? (
                <div>
                  <p className="account-formal-quote-approved">
                    Approved {quote.approved_at !== null
                      ? new Date(quote.approved_at).toLocaleString()
                      : ""}
                  </p>
                  {quote.shipping_insurance_offered ? (
                    <p className="account-muted">
                      Shipping insurance: {quote.shipping_insurance_decision ?? "not recorded"}
                      {quote.shipping_insurance_decided_at !== null
                        ? ` · recorded ${new Date(quote.shipping_insurance_decided_at).toLocaleString()}`
                        : ""}
                    </p>
                  ) : null}
                  {orders.find((order) => order.formal_quote_id === quote.id) !== undefined ? (
                    <p className="account-muted">
                      Order prepared · awaiting secure payment.
                    </p>
                  ) : null}
                </div>
              ) : (
                <p className="account-muted">This revision has been superseded.</p>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
