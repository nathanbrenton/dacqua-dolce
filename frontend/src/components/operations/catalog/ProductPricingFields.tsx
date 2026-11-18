// Pricing policy and scheduled promotions for one catalog product. Part of the
// Catalog workspace; rendered by CatalogProductCard.
//
// API: updateProductPricing, scheduleProductPromotion, cancelProductPromotion
//   in api/operations.ts -> /api/operations/catalog/products/{id}/pricing and /promotions
// Money parsing/formatting: ../operationsMoney.ts; amount input: ../MoneyInput.tsx

import { type ChangeEvent, useState } from "react";
import {
  type OperationsProduct,
  cancelProductPromotion,
  scheduleProductPromotion,
  updateProductPricing,
} from "../../../api/operations";
import { MoneyInput } from "../MoneyInput";
import { formatMoney } from "../operationsMoney";
import { type OperationsNoticeProps, type SaveState } from "../operationsShared";
import {
  AMOUNT_REQUIRED,
  EMPTY_PROMOTION_DRAFT,
  PRICING_MODES,
  PRICING_MODE_LABELS,
  PROMOTION_SUPPORTED_MODES,
  type PricingDraft,
  dollarsToMinor,
  pricingDraftFrom,
} from "./catalogConstants";

type ProductPricingFieldsProps = {
  product: OperationsProduct;
  privileged: boolean;
  onProductChange: (product: OperationsProduct) => void;
} & OperationsNoticeProps;

export function ProductPricingFields({
  product,
  privileged,
  onProductChange,
  onMessage: setMessage,
  onError: setError,
}: ProductPricingFieldsProps) {
  const [pricing, setPricing] = useState(() => pricingDraftFrom(product));
  const [promotion, setPromotion] = useState(EMPTY_PROMOTION_DRAFT);
  const [pricingSaveState, setPricingSaveState] = useState<SaveState>("idle");
  const [promotionSaveState, setPromotionSaveState] = useState<SaveState>("idle");

  const amountNeeded = AMOUNT_REQUIRED.has(pricing.mode);
  const promotionSupported =
    PROMOTION_SUPPORTED_MODES.has(product.standard_pricing.mode)
    && product.standard_pricing.amount_minor !== null;

  async function savePricing() {
    const draft = pricing;

    setError(null);
    setMessage(null);
    setPricingSaveState("saving");

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

      onProductChange(updated);
      setPricing(pricingDraftFrom(updated));
      setMessage(`Pricing policy saved for ${updated.sku}.`);
      setPricingSaveState("saved");

      window.setTimeout(() => {
        setPricingSaveState("idle");
      }, 1800);
    } catch (caught) {
      setPricingSaveState("idle");
      setError(
        caught instanceof Error
          ? caught.message
          : "Pricing update failed.",
      );
    }
  }

  async function schedulePromotion() {
    const draft = promotion;

    setError(null);
    setMessage(null);
    setPromotionSaveState("saving");

    try {
      const amountMinor = dollarsToMinor(draft.amount);
      if (amountMinor === null) {
        throw new Error("Enter a promotional price.");
      }
      if (!draft.startLocal || !draft.endLocal) {
        throw new Error("Enter both promotion start and end times.");
      }

      const updated = await scheduleProductPromotion(product.id, {
        amount_minor: amountMinor,
        effective_from: new Date(draft.startLocal).toISOString(),
        effective_until: new Date(draft.endLocal).toISOString(),
      });

      onProductChange(updated);
      setPricing(pricingDraftFrom(updated));
      setPromotion(EMPTY_PROMOTION_DRAFT);
      setPromotionSaveState("saved");
      setMessage(`Promotion scheduled for ${updated.sku}.`);
      window.setTimeout(() => {
        setPromotionSaveState("idle");
      }, 1800);
    } catch (caught) {
      setPromotionSaveState("idle");
      setError(
        caught instanceof Error
          ? caught.message
          : "Promotion scheduling failed.",
      );
    }
  }

  async function cancelPromotion(
    promotionId: string,
  ) {
    setError(null);
    setMessage(null);
    try {
      const updated = await cancelProductPromotion(product.id, promotionId);
      onProductChange(updated);
      setMessage(`Promotion cancelled for ${updated.sku}.`);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Promotion cancellation failed.",
      );
    }
  }

  function updatePricingDraft(field: keyof PricingDraft, value: string) {
    setPricing((current) => ({ ...current, [field]: value }));
  }

  return (
    <fieldset>
      <legend>Pricing policy</legend>

      <label className="operations-field">
        <span>Mode</span>
        <select
          value={pricing.mode}
          disabled={!privileged}
          onChange={(event: ChangeEvent<HTMLSelectElement>) => {
            updatePricingDraft(
              "mode",
              event.target.value,
            );
          }}
        >
          {PRICING_MODES.map((mode) => (
            <option key={mode} value={mode}>
              {PRICING_MODE_LABELS[mode] ?? mode}
            </option>
          ))}
        </select>
      </label>

      <div className="operations-field-row">
        <label className="operations-field">
          <span>Amount</span>
          <MoneyInput
                                      placeholder={amountNeeded ? "0.00" : "Hidden"}
            value={amountNeeded ? pricing.amount : ""}
            disabled={!privileged || !amountNeeded}
            onChange={(event: ChangeEvent<HTMLInputElement>) => {
              updatePricingDraft(
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
                "currency",
                event.target.value.toUpperCase(),
              );
            }}
          />
        </label>
      </div>

      <p className="operations-governance-context">
        Standard pricing: {PRICING_MODE_LABELS[product.standard_pricing.mode] ?? product.standard_pricing.mode}
        {product.standard_pricing.amount_minor !== null
          ? ` · ${formatMoney(product.standard_pricing.amount_minor, product.standard_pricing.currency ?? "USD")}`
          : " · amount withheld"}
      </p>

      {product.pricing.effective_until !== null ? (
        <p className="operations-governance-context operations-effective-promotion">
          Effective now: {formatMoney(
            product.pricing.amount_minor ?? 0,
            product.pricing.currency ?? "USD",
          )} promotional price through {new Date(product.pricing.effective_until).toLocaleString()}.
        </p>
      ) : null}

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
        onClick={() => void savePricing()}
      >
        {pricingSaveState === "saving"
          ? "Saving…"
          : pricingSaveState === "saved"
            ? "Saved ✓"
            : "Save Pricing Policy"}
      </button>

      {!privileged ? (
        <p className="operations-note">
          Administrator or developer role required
          to change pricing.
        </p>
      ) : null}

      <div className="operations-promotion-panel">
        <div>
          <strong>Temporary promotional pricing</strong>
          <p className="operations-note">
            Promotions are manual, time-bounded overrides of the standard price.
            Customer-specific pricing remains quote-specific rather than an automatic
            account discount.
          </p>
        </div>

        {product.promotions.length > 0 ? (
          <div className="operations-promotion-list">
            {product.promotions.map((scheduled) => (
              <div key={scheduled.id} className="operations-promotion-row">
                <div>
                  <strong>{formatMoney(scheduled.amount_minor, scheduled.currency)}</strong>
                  <span>
                    {scheduled.state === "active" ? "Active" : "Scheduled"}
                    {" · "}
                    {new Date(scheduled.effective_from).toLocaleString()}
                    {" → "}
                    {new Date(scheduled.effective_until).toLocaleString()}
                  </span>
                </div>
                {privileged ? (
                  <button
                    type="button"
                    className="operations-action secondary"
                    onClick={() => {
                      void cancelPromotion(scheduled.id);
                    }}
                  >
                    Cancel promotion
                  </button>
                ) : null}
              </div>
            ))}
          </div>
        ) : (
          <p className="operations-note">No active or scheduled promotion.</p>
        )}

        {promotionSupported ? (
          <div className="operations-promotion-create">
            <label className="operations-field">
              <span>Promotional price</span>
              <MoneyInput
                placeholder="0.00"
                value={promotion.amount}
                disabled={!privileged}
                onChange={(event: ChangeEvent<HTMLInputElement>) => {
                  setPromotion({
                    ...promotion,
                    amount: event.target.value,
                  });
                }}
              />
            </label>
            <label className="operations-field">
              <span>Starts</span>
              <input
                type="datetime-local"
                value={promotion.startLocal}
                disabled={!privileged}
                onChange={(event: ChangeEvent<HTMLInputElement>) => {
                  setPromotion({
                    ...promotion,
                    startLocal: event.target.value,
                  });
                }}
              />
            </label>
            <label className="operations-field">
              <span>Ends</span>
              <input
                type="datetime-local"
                value={promotion.endLocal}
                disabled={!privileged}
                onChange={(event: ChangeEvent<HTMLInputElement>) => {
                  setPromotion({
                    ...promotion,
                    endLocal: event.target.value,
                  });
                }}
              />
            </label>
            <button
              type="button"
              className={
                "operations-action "
                + (promotionSaveState === "saved" ? "is-saved" : "")
              }
              disabled={!privileged || promotionSaveState === "saving"}
              onClick={() => void schedulePromotion()}
            >
              {promotionSaveState === "saving"
                ? "Scheduling…"
                : promotionSaveState === "saved"
                  ? "Scheduled ✓"
                  : "Schedule promotion"}
            </button>
          </div>
        ) : (
          <p className="operations-note">
            {product.standard_pricing.mode === "MAP_LIMITED"
              ? "MAP-limited promotions stay disabled until verified manufacturer promotional terms are recorded; do not infer a permissible advertised discount."
              : "Scheduled promotions require a standard PUBLIC, CART_ONLY, or LOGIN_REQUIRED price with an authoritative amount."}
          </p>
        )}
      </div>
    </fieldset>
  );
}
