// Stripe Tax product classification for one catalog product. Part of the
// Catalog workspace; rendered by CatalogProductCard.
//
// API: updateProductTaxClassification in api/operations.ts
//   -> /api/operations/catalog/products/{id}/tax-classification

import { type ChangeEvent, useState } from "react";
import {
  type OperationsProduct,
  updateProductTaxClassification,
} from "../../../api/operations";
import { type OperationsNoticeProps, type SaveState } from "../operationsShared";
import { taxClassificationDraftFrom } from "./catalogConstants";
import { exactEntryProps } from "../../forms/textEntry";

type ProductTaxFieldsProps = {
  product: OperationsProduct;
  privileged: boolean;
  onProductChange: (product: OperationsProduct) => void;
} & OperationsNoticeProps;

export function ProductTaxFields({
  product,
  privileged,
  onProductChange,
  onMessage: setMessage,
  onError: setError,
}: ProductTaxFieldsProps) {
  const [taxClassification, setTaxClassification] =
    useState(() => taxClassificationDraftFrom(product));
  const [taxClassificationSaveState, setTaxClassificationSaveState] =
    useState<SaveState>("idle");

  async function saveTaxClassification() {
    const draft = taxClassification;

    const taxCode = draft.taxCode.trim();
    const sourceReference = draft.sourceReference.trim();
    if (!taxCode.startsWith("txcd_")) {
      setError("Enter an exact Stripe Tax product tax code beginning with txcd_.");
      return;
    }
    if (sourceReference.length === 0) {
      setError("Record the authoritative source used for this tax classification.");
      return;
    }

    setError(null);
    setMessage(null);
    setTaxClassificationSaveState("saving");

    try {
      const updated = await updateProductTaxClassification(product.id, {
        tax_code: taxCode,
        source_reference: sourceReference,
      });
      onProductChange(updated);
      setTaxClassification(taxClassificationDraftFrom(updated));
      setMessage(`Tax classification saved for ${updated.sku}.`);
      setTaxClassificationSaveState("saved");
      window.setTimeout(() => {
        setTaxClassificationSaveState("idle");
      }, 1800);
    } catch (caught) {
      setTaxClassificationSaveState("idle");
      setError(
        caught instanceof Error
          ? caught.message
          : "Tax classification update failed.",
      );
    }
  }

  return (
    <fieldset>
      <legend>Automated tax classification</legend>

      <p className="operations-note">
        Record an exact Stripe Tax product tax code and the authoritative
        source used to classify this product. D’Acqua Dolce does not infer
        a product tax code. PT44 remains sandbox-only; live tax collection
        stays blocked until registrations and production commissioning are complete.
      </p>

      <label className="operations-field">
        <span>Stripe Tax code</span>
        <input
          {...exactEntryProps}
          placeholder="txcd_…"
          value={taxClassification.taxCode}
          disabled={!privileged}
          onChange={(event: ChangeEvent<HTMLInputElement>) => {
            setTaxClassification({
              ...taxClassification,
              taxCode: event.target.value,
            });
          }}
        />
      </label>

      <label className="operations-field">
        <span>Classification source</span>
        <input
          {...exactEntryProps}
          placeholder="Stripe tax-code catalog / reviewed source"
          value={taxClassification.sourceReference}
          disabled={!privileged}
          onChange={(event: ChangeEvent<HTMLInputElement>) => {
            setTaxClassification({
              ...taxClassification,
              sourceReference: event.target.value,
            });
          }}
        />
      </label>

      {product.tax_classification !== null ? (
        <p className="operations-governance-context">
          Verified {new Date(product.tax_classification.verified_at).toLocaleString()}
          {" · "}
          {product.tax_classification.provider}
        </p>
      ) : (
        <p className="operations-governance-context">
          No authoritative automated-tax classification recorded.
        </p>
      )}

      <button
        type="button"
        className={
          "operations-action "
          + (taxClassificationSaveState === "saved" ? "is-saved" : "")
        }
        disabled={!privileged || taxClassificationSaveState === "saving"}
        onClick={() => void saveTaxClassification()}
      >
        {taxClassificationSaveState === "saving"
          ? "Saving…"
          : taxClassificationSaveState === "saved"
            ? "Saved ✓"
            : "Save tax classification"}
      </button>

      {!privileged ? (
        <p className="operations-note">
          Administrator or developer role required to change tax classification.
        </p>
      ) : null}
    </fieldset>
  );
}
