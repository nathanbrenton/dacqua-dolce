import {
  useMemo,
  useState,
} from "react";

import {
  reviewOrderCancellation,
  type OperationsOrder,
  updateOrderFulfillment,
} from "../../api/operations";

type Props = {
  order: OperationsOrder;
  onUpdated: (order: OperationsOrder) => void;
};

const FULFILLMENT_LABELS: Record<string, string> = {
  not_started: "Not started",
  supplier_ordered: "Equipment ordered from supplier",
  received_ready: "Equipment received / ready",
  shipped: "Shipped",
  delivered: "Delivered",
};

function label(value: string): string {
  return FULFILLMENT_LABELS[value] ?? value.replaceAll("_", " ");
}

export function OrderFulfillmentControls({
  order,
  onUpdated,
}: Props) {
  const [supplierReference, setSupplierReference] =
    useState(order.supplier_order_reference ?? "");
  const [carrier, setCarrier] =
    useState(order.shipment?.carrier ?? "");
  const [trackingNumber, setTrackingNumber] =
    useState(order.shipment?.tracking_number ?? "");
  const [trackingUrl, setTrackingUrl] =
    useState(order.shipment?.tracking_url ?? "");
  const [saving, setSaving] = useState(false);
  const [cancellationSaving, setCancellationSaving] =
    useState(false);
  const [reviewNote, setReviewNote] =
    useState(order.cancellation?.review_note ?? "");
  const [error, setError] =
    useState<string | null>(null);

  const nextStatus = useMemo(() => {
    switch (order.fulfillment_status) {
      case "not_started":
        return "supplier_ordered";
      case "supplier_ordered":
        return "received_ready";
      case "received_ready":
        return "shipped";
      case "shipped":
        return "delivered";
      default:
        return null;
    }
  }, [order.fulfillment_status]);

  const supplierOrderingBlocked =
    order.fulfillment_status === "not_started"
    && order.cancellation !== null
    && order.cancellation.status !== "declined";

  async function reviewCancellation(
    action: "approve" | "decline" | "complete",
  ): Promise<void> {
    setCancellationSaving(true);
    setError(null);

    try {
      const updated = await reviewOrderCancellation(
        order.id,
        {
          action,
          note: reviewNote.trim() || null,
        },
      );
      onUpdated(updated);
      setReviewNote(updated.cancellation?.review_note ?? "");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Cancellation update failed.",
      );
    } finally {
      setCancellationSaving(false);
    }
  }

  async function advance(): Promise<void> {
    if (nextStatus === null) {
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const updated = await updateOrderFulfillment(
        order.id,
        {
          status: nextStatus,
          supplier_order_reference:
            nextStatus === "supplier_ordered"
              ? supplierReference || null
              : undefined,
          carrier:
            nextStatus === "shipped"
              ? carrier || null
              : undefined,
          tracking_number:
            nextStatus === "shipped"
              ? trackingNumber || null
              : undefined,
          tracking_url:
            nextStatus === "shipped"
              ? trackingUrl || null
              : undefined,
        },
      );
      onUpdated(updated);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Fulfillment update failed.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="order-fulfillment-controls">
      <div className="order-fulfillment-summary">
        <span>
          <strong>Payment:</strong>{" "}
          {order.status.replaceAll("_", " ")}
        </span>
        <span>
          <strong>Fulfillment:</strong>{" "}
          {label(order.fulfillment_status)}
        </span>
      </div>

      <div className="order-cancellation-operations">
        <div>
          <strong>Cancellation</strong>
          <span>
            {order.cancellation === null
              ? order.cancellation_mode === "unrestricted"
                ? "No request · unrestricted before supplier confirmation"
                : "No request · manual review after supplier confirmation"
              : `${order.cancellation.status.replaceAll("_", " ")} · ${
                  order.cancellation.eligibility_mode === "unrestricted"
                    ? "pre-supplier"
                    : "post-supplier review"
                }`}
          </span>
        </div>

        {order.cancellation?.reason ? (
          <p className="account-muted">
            Customer reason: {order.cancellation.reason}
          </p>
        ) : null}

        {order.cancellation?.status === "requested" ? (
          <>
            <label className="operations-field">
              <span>Cancellation review note (optional)</span>
              <textarea
                rows={3}
                maxLength={4000}
                value={reviewNote}
                onChange={(event) => {
                  setReviewNote(event.target.value);
                }}
              />
            </label>
            <div className="order-cancellation-actions">
              <button
                type="button"
                className="secondary-button"
                disabled={cancellationSaving}
                onClick={() => {
                  void reviewCancellation("approve");
                }}
              >
                Approve cancellation
              </button>
              <button
                type="button"
                className="secondary-button"
                disabled={cancellationSaving}
                onClick={() => {
                  void reviewCancellation("decline");
                }}
              >
                Decline cancellation
              </button>
            </div>
          </>
        ) : null}

        {order.cancellation?.status === "approved" ? (
          <>
            <p className="account-muted">
              Cancellation is approved. Payment reversal/void is not automated;
              complete any required payment or administrative action separately.
            </p>
            <button
              type="button"
              className="secondary-button"
              disabled={cancellationSaving}
              onClick={() => {
                void reviewCancellation("complete");
              }}
            >
              {cancellationSaving
                ? "Saving…"
                : "Mark cancellation complete"}
            </button>
          </>
        ) : null}

        {order.cancellation?.status === "declined" ? (
          <p className="account-muted">
            Cancellation was reviewed and declined.
            Fulfillment may continue.
          </p>
        ) : null}

        {order.cancellation?.status === "completed" ? (
          <p className="account-muted">
            Cancellation workflow is complete.
          </p>
        ) : null}
      </div>

      {order.status !== "paid" ? (
        <p className="account-muted">
          Fulfillment advances after payment is confirmed.
        </p>
      ) : null}

      {order.status === "paid"
        && order.fulfillment_status === "not_started"
        && !supplierOrderingBlocked ? (
        <label className="operations-field">
          <span>Supplier order reference (optional)</span>
          <input
            type="text"
            value={supplierReference}
            maxLength={160}
            onChange={(event) => {
              setSupplierReference(event.target.value);
            }}
          />
        </label>
      ) : null}

      {supplierOrderingBlocked ? (
        <p className="operations-alert" role="status">
          Supplier ordering is blocked while this cancellation is active.
        </p>
      ) : null}

      {order.status === "paid"
        && order.fulfillment_status === "received_ready" ? (
        <div className="order-fulfillment-shipping-fields">
          <label className="operations-field">
            <span>Carrier</span>
            <input
              type="text"
              value={carrier}
              maxLength={100}
              onChange={(event) => {
                setCarrier(event.target.value);
              }}
            />
          </label>

          <label className="operations-field">
            <span>Tracking number</span>
            <input
              type="text"
              value={trackingNumber}
              maxLength={200}
              onChange={(event) => {
                setTrackingNumber(event.target.value);
              }}
            />
          </label>

          <label className="operations-field">
            <span>Tracking URL (optional HTTPS)</span>
            <input
              type="url"
              value={trackingUrl}
              maxLength={2048}
              onChange={(event) => {
                setTrackingUrl(event.target.value);
              }}
            />
          </label>
        </div>
      ) : null}

      {order.shipment !== null ? (
        <div className="order-tracking-summary">
          <strong>
            {order.shipment.carrier}
          </strong>
          <span>
            {order.shipment.tracking_number}
          </span>
          {order.shipment.tracking_url !== null ? (
            <a
              href={order.shipment.tracking_url}
              target="_blank"
              rel="noreferrer"
            >
              Open carrier tracking
            </a>
          ) : null}
        </div>
      ) : null}

      {error !== null ? (
        <p className="form-error" role="alert">
          {error}
        </p>
      ) : null}

      {order.status === "paid"
        && nextStatus !== null ? (
        <button
          type="button"
          className="secondary-button"
          disabled={saving || supplierOrderingBlocked}
          onClick={() => {
            void advance();
          }}
        >
          {saving
            ? "Saving…"
            : `Mark ${label(nextStatus)}`}
        </button>
      ) : null}
    </div>
  );
}
