// Lifecycle (active / soon discontinued / discontinued), unavailable-product
// exceptions and inventory for one catalog product. Part of the Catalog
// workspace; rendered by CatalogProductCard. Saving inventory as available
// sends waiting Notify When in Stock notices server-side, so the workspace
// refreshes that list via onInventorySaved.
//
// API: updateProductAvailabilityPolicy, updateProductInventory in api/operations.ts
//   -> /api/operations/catalog/products/{id}/availability-policy and /inventory

import { type ChangeEvent, useState } from "react";
import {
  type OperationsProduct,
  updateProductAvailabilityPolicy,
  updateProductInventory,
} from "../../../api/operations";
import { type OperationsNoticeProps, type SaveState } from "../operationsShared";
import {
  type AvailabilityPolicyDraft,
  INVENTORY_SOURCE_KINDS,
  INVENTORY_SOURCE_LABELS,
  INVENTORY_STATUSES,
  INVENTORY_STATUS_LABELS,
  type InventoryDraft,
  PRODUCT_LIFECYCLE_LABELS,
  PRODUCT_LIFECYCLE_STATUSES,
  availabilityPolicyDraftFrom,
  inventoryDraftFrom,
} from "./catalogConstants";

type ProductAvailabilityFieldsProps = {
  onInventorySaved: () => void;
  product: OperationsProduct;
  privileged: boolean;
  onProductChange: (product: OperationsProduct) => void;
} & OperationsNoticeProps;

export function ProductAvailabilityFields({
  onInventorySaved,
  product,
  privileged,
  onProductChange,
  onMessage: setMessage,
  onError: setError,
}: ProductAvailabilityFieldsProps) {
  const [availabilityPolicy, setAvailabilityPolicy] =
    useState(() => availabilityPolicyDraftFrom(product));
  const [inventory, setInventory] = useState(() => inventoryDraftFrom(product));
  const [availabilityPolicySaveState, setAvailabilityPolicySaveState] =
    useState<SaveState>("idle");
  const [inventorySaveState, setInventorySaveState] =
    useState<SaveState>("idle");

  async function saveAvailabilityPolicy() {
    const draft = availabilityPolicy;

    setError(null);
    setMessage(null);
    setAvailabilityPolicySaveState("saving");

    try {
      const updated = await updateProductAvailabilityPolicy(
        product.id,
        {
          lifecycle_status: draft.lifecycleStatus,
          public_retire_at: draft.publicRetireLocal.length === 0
            ? null
            : new Date(draft.publicRetireLocal).toISOString(),
          allow_inquiry_when_unavailable: draft.allowInquiryWhenUnavailable,
          allow_formal_quote_when_unavailable: draft.allowFormalQuoteWhenUnavailable,
        },
      );

      onProductChange(updated);
      setAvailabilityPolicy(availabilityPolicyDraftFrom(updated));
      setMessage(`Availability policy saved for ${updated.sku}.`);
      setAvailabilityPolicySaveState("saved");

      window.setTimeout(() => {
        setAvailabilityPolicySaveState("idle");
      }, 1800);
    } catch (caught) {
      setAvailabilityPolicySaveState("idle");
      setError(
        caught instanceof Error
          ? caught.message
          : "Availability policy update failed.",
      );
    }
  }

  async function saveInventory() {
    const draft = inventory;

    setError(null);
    setMessage(null);

    const quantityOnHand = Number.parseInt(
      draft.quantityOnHand,
      10,
    );

    if (
      !Number.isInteger(quantityOnHand)
      || quantityOnHand < 0
    ) {
      setError(
        "On-hand quantity must be a non-negative integer.",
      );
      return;
    }

    setInventorySaveState("saving");

    try {
      const updated = await updateProductInventory(
        product.id,
        {
          status: draft.status,
          quantity_on_hand: quantityOnHand,
          expected_available_on: draft.expectedAvailableOn || null,
          estimated_lead_time: (
            draft.estimatedLeadTime.trim() || null
          ),
          source_kind: draft.sourceKind,
          source_reference: draft.sourceReference.trim() || null,
        },
      );

      onProductChange(updated);
      setInventory(inventoryDraftFrom(updated));
      setMessage(`Inventory saved for ${updated.sku}.`);
      onInventorySaved();
      setInventorySaveState("saved");

      window.setTimeout(() => {
        setInventorySaveState("idle");
      }, 1800);
    } catch (caught) {
      setInventorySaveState("idle");
      setError(
        caught instanceof Error
          ? caught.message
          : "Inventory update failed.",
      );
    }
  }

  function updateAvailabilityPolicyDraft(patch: Partial<AvailabilityPolicyDraft>) {
    setAvailabilityPolicy((current) => ({ ...current, ...patch }));
  }

  function updateInventoryDraft<K extends keyof InventoryDraft>(
    field: K,
    value: InventoryDraft[K],
  ) {
    setInventory((current) => ({ ...current, [field]: value }));
  }

  return (
    <fieldset>
      <legend>Availability lifecycle &amp; inventory</legend>

      <div className="operations-availability-policy">
        <label className="operations-field">
          <span>Product lifecycle</span>
          <select
            value={availabilityPolicy.lifecycleStatus}
            disabled={!privileged}
            onChange={(event: ChangeEvent<HTMLSelectElement>) => {
              updateAvailabilityPolicyDraft({
                lifecycleStatus: event.target.value as OperationsProduct["lifecycle_status"],
              });
            }}
          >
            {PRODUCT_LIFECYCLE_STATUSES.map((lifecycleStatus) => (
              <option key={lifecycleStatus} value={lifecycleStatus}>
                {PRODUCT_LIFECYCLE_LABELS[lifecycleStatus]}
              </option>
            ))}
          </select>
          <small>Discontinued is distinct from a temporary stock shortage.</small>
        </label>

        <label className="operations-field">
          <span>Remove from public catalog at</span>
          <input
            type="datetime-local"
            value={availabilityPolicy.publicRetireLocal}
            disabled={
              !privileged
              || availabilityPolicy.lifecycleStatus !== "discontinued"
            }
            onChange={(event) => {
              updateAvailabilityPolicyDraft({
                publicRetireLocal: event.target.value,
              });
            }}
          />
          <small>
            Optional. Leave blank to keep the discontinued product public.
            At the configured time it disappears from customer catalog
            routes while its internal/history record remains.
          </small>
        </label>

        <p className="operations-note">
          Public catalog state: {product.public_catalog_visible
            ? "visible"
            : "retired from customer-facing catalog"}
          {product.public_retire_at !== null
            ? ` · scheduled ${new Date(product.public_retire_at).toLocaleString()}`
            : ""}.
        </p>

        <label className="operations-checkbox-row">
          <input
            type="checkbox"
            checked={availabilityPolicy.allowInquiryWhenUnavailable}
            disabled={!privileged}
            onChange={(event) => {
              updateAvailabilityPolicyDraft({
                allowInquiryWhenUnavailable: event.target.checked,
              });
            }}
          />
          <span>Allow customer inquiry while unavailable</span>
        </label>

        <label className="operations-checkbox-row">
          <input
            type="checkbox"
            checked={availabilityPolicy.allowFormalQuoteWhenUnavailable}
            disabled={!privileged}
            onChange={(event) => {
              updateAvailabilityPolicyDraft({
                allowFormalQuoteWhenUnavailable: event.target.checked,
              });
            }}
          />
          <span>Allow staff to create a formal quote while unavailable</span>
        </label>

        <p className="operations-note">
          Default launch behavior keeps inquiries available but blocks formal quotes when a product is out of stock or discontinued. Enable the formal-quote exception only when staff has confirmed the product can still be fulfilled.
        </p>

        <button
          type="button"
          className={
            "operations-action secondary "
            + (availabilityPolicySaveState === "saved" ? "is-saved" : "")
          }
          disabled={!privileged || availabilityPolicySaveState === "saving"}
          onClick={() => void saveAvailabilityPolicy()}
        >
          {availabilityPolicySaveState === "saving"
            ? "Saving…"
            : availabilityPolicySaveState === "saved"
              ? "Saved ✓"
              : "Save Availability Policy"}
        </button>
      </div>

      <label className="operations-field">
        <span>Status</span>
        <select
          value={inventory.status}
          disabled={!privileged}
          onChange={(event: ChangeEvent<HTMLSelectElement>) => {
            updateInventoryDraft(
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
              {INVENTORY_STATUS_LABELS[inventoryStatus] ?? inventoryStatus}
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
            disabled={!privileged}
            onChange={(event: ChangeEvent<HTMLInputElement>) => {
              updateInventoryDraft(
                "quantityOnHand",
                event.target.value,
              );
            }}
          />
        </label>

        <label className="operations-field">
          <span>Reserved · automatic</span>
          <input
            type="number"
            min={0}
            step={1}
            value={
              product.inventory.quantity_reserved
            }
            readOnly
            aria-readonly="true"
          />
          <small>
            Active, unexpired cart holds
          </small>
        </label>
      </div>

      <label className="operations-field">
        <span>Expected availability date · use when known</span>
        <input
          type="date"
          value={inventory.expectedAvailableOn}
          disabled={!privileged}
          onChange={(event: ChangeEvent<HTMLInputElement>) => {
            updateInventoryDraft(
              "expectedAvailableOn",
              event.target.value,
            );
            if (event.target.value !== "") {
              updateInventoryDraft(
                "estimatedLeadTime",
                "",
              );
            }
          }}
        />
      </label>

      <label className="operations-field">
        <span>Estimated availability range · use when date is unknown</span>
        <input
          type="text"
          maxLength={120}
          placeholder="Example: 2–3 weeks"
          value={inventory.estimatedLeadTime}
          disabled={!privileged || inventory.expectedAvailableOn !== ""}
          onChange={(event: ChangeEvent<HTMLInputElement>) => {
            updateInventoryDraft(
              "estimatedLeadTime",
              event.target.value,
            );
          }}
        />
        <small>
          The customer sees the expected date when known; otherwise this range. Leave both blank until timing is reliable.
        </small>
      </label>

      <div className="operations-field-row">
        <label className="operations-field">
          <span>Inventory information source</span>
          <select
            value={inventory.sourceKind}
            disabled={!privileged}
            onChange={(event: ChangeEvent<HTMLSelectElement>) => {
              updateInventoryDraft(
                "sourceKind",
                event.target.value as InventoryDraft["sourceKind"],
              );
            }}
          >
            {INVENTORY_SOURCE_KINDS.map((sourceKind) => (
              <option key={sourceKind} value={sourceKind}>
                {INVENTORY_SOURCE_LABELS[sourceKind]}
              </option>
            ))}
          </select>
        </label>

        <label className="operations-field">
          <span>Internal source reference</span>
          <input
            type="text"
            maxLength={240}
            placeholder="Portal, rep, report, or internal count"
            value={inventory.sourceReference}
            disabled={!privileged}
            onChange={(event: ChangeEvent<HTMLInputElement>) => {
              updateInventoryDraft(
                "sourceReference",
                event.target.value,
              );
            }}
          />
          <small>Internal only; never shown to customers.</small>
        </label>
      </div>

      <p className="operations-governance-context">
        Source: {INVENTORY_SOURCE_LABELS[product.inventory.source_kind] ?? product.inventory.source_kind}
        {product.inventory.source_observed_at !== null
          ? ` · checked ${new Date(product.inventory.source_observed_at).toLocaleString()}`
          : " · not yet timestamped"}
      </p>

      <p className="operations-governance-context">
        Authoritative stock: {product.inventory.quantity_on_hand}
        {product.inventory.status !== "not_tracked"
          ? ` · reserved ${product.inventory.quantity_reserved} · available ${Math.max(0, product.inventory.quantity_on_hand - product.inventory.quantity_reserved)}`
          : " · quantity is informational while inventory is not tracked"}
      </p>

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
          !privileged
          || inventorySaveState === "saving"
        }
        onClick={() => void saveInventory()}
      >
        {inventorySaveState === "saving"
          ? "Saving…"
          : inventorySaveState === "saved"
            ? "Saved ✓"
            : "Save Inventory"}
      </button>

      {!privileged ? (
        <p className="operations-note">
          Administrator or developer role required
          to change inventory.
        </p>
      ) : null}
    </fieldset>
  );
}
