// Options, accessories & consumables linked to one catalog product (internal
// until made public). Part of the Catalog workspace; rendered by CatalogProductCard.
//
// API: createProductRelationship / updateProductRelationship / deleteProductRelationship
//   in api/operations.ts -> /api/operations/catalog/products/{id}/relationships
// Styles: .operations-product-relationship* in styles.css

import { type ChangeEvent, useState } from "react";

import {
  createProductRelationship,
  deleteProductRelationship,
  updateProductRelationship,
  type OperationsProduct,
} from "../../../api/operations";
import type { OperationsNoticeProps, SaveState } from "../operationsShared";
import { exactEntryProps } from "../../forms/textEntry";

type ProductRelationshipsProps = {
  products: OperationsProduct[];
  product: OperationsProduct;
  privileged: boolean;
  onProductChange: (product: OperationsProduct) => void;
} & OperationsNoticeProps;

export function ProductRelationships({
  products,
  product,
  privileged,
  onProductChange,
  onMessage: setMessage,
  onError: setError,
}: ProductRelationshipsProps) {
  const [relationshipProduct, setRelationshipProduct] = useState("");
  const [relationshipType, setRelationshipType] =
    useState<"option" | "accessory" | "replacement">("option");
  const [relationshipSaveState, setRelationshipSaveState] =
    useState<SaveState>("idle");

  async function addProductRelationship() {
    const relatedProductId = relationshipProduct;

    if (relatedProductId.length === 0) {
      setError("Choose a related catalog product first.");
      return;
    }

    setError(null);
    setMessage(null);
    setRelationshipSaveState("saving");

    try {
      const updated = await createProductRelationship(product.id, {
        related_product_id: relatedProductId,
        relationship_type: relationshipType,
        public: false,
        active: true,
        is_consumable: false,
        replacement_interval_days: null,
        reminder_preference: null,
        sort_order: 0,
      });
      onProductChange(updated);
      setRelationshipProduct("");
      setMessage(`Internal ${relationshipType} added for ${product.sku}.`);
      setRelationshipSaveState("saved");
    } catch (caught) {
      setRelationshipSaveState("idle");
      setError(
        caught instanceof Error
          ? caught.message
          : "Product relationship update failed.",
      );
    }
  }

  async function changeProductRelationship(
    relationship: OperationsProduct["relationships"][number],
    changes: Partial<{
      public: boolean;
      active: boolean;
      is_consumable: boolean;
      replacement_interval_days: number | null;
      reminder_preference:
        | "filter_replacement"
        | "uv_service"
        | "product_specific"
        | null;
    }>,
  ) {
    setError(null);
    setMessage(null);

    try {
      const updated = await updateProductRelationship(
        product.id,
        relationship.id,
        {
          relationship_type: relationship.relationship_type,
          public: changes.public ?? relationship.public,
          active: changes.active ?? relationship.active,
          is_consumable: changes.is_consumable ?? relationship.is_consumable,
          replacement_interval_days:
            "replacement_interval_days" in changes
              ? changes.replacement_interval_days ?? null
              : relationship.replacement_interval_days,
          reminder_preference:
            "reminder_preference" in changes
              ? changes.reminder_preference ?? null
              : relationship.reminder_preference,
          sort_order: relationship.sort_order,
        },
      );
      onProductChange(updated);
      setMessage(`Product relationship saved for ${product.sku}.`);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Product relationship update failed.",
      );
    }
  }

  async function removeProductRelationship(
    relationshipId: string,
  ) {
    setError(null);
    setMessage(null);

    try {
      const updated = await deleteProductRelationship(
        product.id,
        relationshipId,
      );
      onProductChange(updated);
      setMessage(`Product relationship removed from ${product.sku}.`);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Product relationship removal failed.",
      );
    }
  }

  return (
    <details className="operations-product-relationships">
      <summary>Options, accessories &amp; consumables</summary>

      <div className="operations-product-relationship-list">
        {product.relationships.length === 0 ? (
          <p className="operations-note">
            No product relationships are recorded. Add only options, accessories, or replacement items whose compatibility has been verified.
          </p>
        ) : (
          product.relationships.map((relationship) => (
            <div
              key={relationship.id}
              className="operations-product-relationship"
            >
              <div>
                <strong>{relationship.related_name}</strong>
                <code>{relationship.related_sku}</code>
                <small>
                  {relationship.relationship_type === "option"
                    ? "Option"
                    : relationship.relationship_type === "accessory"
                      ? "Accessory"
                      : "Replacement"}
                  {relationship.active ? " · active" : " · inactive"}
                  {relationship.public ? " · public" : " · internal"}
                  {relationship.is_consumable ? " · consumable" : ""}
                  {relationship.replacement_interval_days !== null
                    ? ` · ${relationship.replacement_interval_days}-day interval`
                    : ""}
                  {relationship.reminder_preference !== null
                    ? ` · ${relationship.reminder_preference.replaceAll("_", " ")} reminder`
                    : ""}
                </small>
              </div>

              {privileged ? (
                <div className="operations-product-relationship-actions">
                  <button
                    type="button"
                    className="operations-action secondary"
                    onClick={() => {
                      void changeProductRelationship(
                        relationship,
                        { public: !relationship.public },
                      );
                    }}
                  >
                    {relationship.public ? "Make internal" : "Make public"}
                  </button>
                  <button
                    type="button"
                    className="operations-action secondary"
                    onClick={() => {
                      void changeProductRelationship(
                        relationship,
                        { active: !relationship.active },
                      );
                    }}
                  >
                    {relationship.active ? "Deactivate" : "Activate"}
                  </button>
                  <button
                    type="button"
                    className="operations-action secondary"
                    onClick={() => {
                      void changeProductRelationship(
                        relationship,
                        {
                          is_consumable: !relationship.is_consumable,
                          replacement_interval_days: null,
                          reminder_preference: null,
                        },
                      );
                    }}
                  >
                    {relationship.is_consumable
                      ? "Remove consumable flag"
                      : "Mark consumable"}
                  </button>
                  {relationship.is_consumable ? (
                    <label className="operations-field compact">
                      <span>Replacement interval (days)</span>
                      <input
                        {...exactEntryProps}
                        type="number"
                        min="1"
                        max="3650"
                        defaultValue={relationship.replacement_interval_days ?? ""}
                        placeholder="Optional"
                        onBlur={(event) => {
                          const raw = event.currentTarget.value.trim();
                          const value = raw.length === 0
                            ? null
                            : Number.parseInt(raw, 10);
                          if (value !== null && (!Number.isInteger(value) || value < 1)) {
                            setError("Replacement interval must be a positive number of days.");
                            return;
                          }
                          void changeProductRelationship(
                            relationship,
                            {
                              replacement_interval_days: value,
                              reminder_preference:
                                value === null
                                  ? null
                                  : relationship.reminder_preference,
                            },
                          );
                        }}
                      />
                    </label>
                  ) : null}
                  {relationship.is_consumable
                    && relationship.replacement_interval_days !== null ? (
                    <label className="operations-field compact">
                      <span>Reminder opt-in</span>
                      <select
                        value={relationship.reminder_preference ?? ""}
                        onChange={(event) => {
                          const value = event.currentTarget.value;
                          void changeProductRelationship(
                            relationship,
                            {
                              reminder_preference:
                                value === ""
                                  ? null
                                  : value as
                                    | "filter_replacement"
                                    | "uv_service"
                                    | "product_specific",
                            },
                          );
                        }}
                      >
                        <option value="">No scheduled reminder</option>
                        <option value="filter_replacement">
                          Filter replacement reminders
                        </option>
                        <option value="uv_service">
                          UV service reminders
                        </option>
                        <option value="product_specific">
                          Product-specific reminders
                        </option>
                      </select>
                    </label>
                  ) : null}
                  <button
                    type="button"
                    className="operations-action secondary"
                    onClick={() => {
                      void removeProductRelationship(
                        relationship.id,
                      );
                    }}
                  >
                    Remove
                  </button>
                </div>
              ) : null}
            </div>
          ))
        )}
      </div>

      {privileged ? (
        <div className="operations-product-relationship-create">
          <label className="operations-field">
            <span>Related catalog product</span>
            <select
              value={relationshipProduct}
              onChange={(event: ChangeEvent<HTMLSelectElement>) => {
                setRelationshipProduct(event.target.value);
              }}
            >
              <option value="">Choose a product</option>
              {products
                .filter((candidate) => candidate.id !== product.id)
                .map((candidate) => (
                  <option key={candidate.id} value={candidate.id}>
                    {candidate.name} · {candidate.sku}
                  </option>
                ))}
            </select>
          </label>

          <label className="operations-field">
            <span>Relationship</span>
            <select
              value={relationshipType}
              onChange={(event: ChangeEvent<HTMLSelectElement>) => {
                setRelationshipType(event.target.value as "option" | "accessory" | "replacement");
              }}
            >
              <option value="option">Option</option>
              <option value="accessory">Accessory</option>
              <option value="replacement">Replacement</option>
            </select>
          </label>

          <button
            type="button"
            className="operations-action"
            disabled={relationshipSaveState === "saving"}
            onClick={() => {
              void addProductRelationship();
            }}
          >
            {relationshipSaveState === "saving"
              ? "Adding…"
              : "Add as internal"}
          </button>
          <p className="operations-note">
            New relationships start internal. Use Replacement only for a verified successor/current product; make it public only after approval. Consumable flags and intervals remain for service/replacement items.
          </p>
        </div>
      ) : null}
    </details>
  );
}
