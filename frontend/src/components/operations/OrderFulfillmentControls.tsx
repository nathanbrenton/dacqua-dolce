import {
  useMemo,
  useState,
} from "react";

import {
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

      {order.status !== "paid" ? (
        <p className="account-muted">
          Fulfillment advances after payment is confirmed.
        </p>
      ) : null}

      {order.status === "paid"
        && order.fulfillment_status === "not_started" ? (
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
          disabled={saving}
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
