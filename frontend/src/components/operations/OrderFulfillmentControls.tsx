import {
  useMemo,
  useState,
} from "react";

import {
  authorizeReturnPolicyException,
  reviewOrderCancellation,
  sendOrderConfirmation,
  startOrderCancellationException,
  type OperationsOrder,
  updateOrderFulfillment,
} from "../../api/operations";

type Props = {
  order: OperationsOrder;
  roles: string[];
  onUpdated: (order: OperationsOrder) => void;
};

const FULFILLMENT_LABELS: Record<string, string> = {
  not_started: "Processing",
  supplier_ordered: "Supplier Confirmed",
  received_ready: "Awaiting Shipment",
  shipped: "Shipped",
  delivered: "Completed",
};

const CUSTOMER_STATUS_LABELS: Record<string, string> = {
  received: "Received",
  processing: "Processing",
  supplier_confirmed: "Supplier Confirmed",
  awaiting_shipment: "Awaiting Shipment",
  shipped: "Shipped",
  completed: "Completed",
  cancelled: "Cancelled",
  refunded: "Refunded",
};

function label(value: string): string {
  return FULFILLMENT_LABELS[value] ?? value.replaceAll("_", " ");
}

function customerStatusLabel(value: string): string {
  return CUSTOMER_STATUS_LABELS[value] ?? value.replaceAll("_", " ");
}

export function OrderFulfillmentControls({
  order,
  roles,
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
  const [confirmationSaving, setConfirmationSaving] = useState(false);
  const [cancellationSaving, setCancellationSaving] =
    useState(false);
  const [reviewNote, setReviewNote] =
    useState(order.cancellation?.review_note ?? "");
  const [exceptionalCancellationReason, setExceptionalCancellationReason] =
    useState("");
  const [exceptionalCancellationSaving, setExceptionalCancellationSaving] =
    useState(false);
  const [error, setError] =
    useState<string | null>(null);
  const [exceptionSaving, setExceptionSaving] =
    useState(false);
  const [exceptionReason, setExceptionReason] =
    useState("");
  const [returnWindowOverride, setReturnWindowOverride] =
    useState("");
  const [restockingPercentOverride, setRestockingPercentOverride] =
    useState("");
  const [returnShippingOverride, setReturnShippingOverride] =
    useState<"" | "customer" | "business">("");
  const [outboundShippingOverride, setOutboundShippingOverride] =
    useState<"" | "nonrefundable" | "refund">("");

  const canAuthorizeReturnException = roles.some(
    (role) => (
      role === "manager"
      || role === "administrator"
      || role === "developer"
    ),
  );
  const canManageCancellationExceptions = canAuthorizeReturnException;

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

  async function startExceptionalCancellationReview(): Promise<void> {
    const reason = exceptionalCancellationReason.trim();
    if (reason === "") {
      setError("A reason is required for exceptional cancellation review.");
      return;
    }

    setExceptionalCancellationSaving(true);
    setError(null);

    try {
      const updated = await startOrderCancellationException(
        order.id,
        reason,
      );
      onUpdated(updated);
      setExceptionalCancellationReason("");
      setReviewNote(updated.cancellation?.review_note ?? "");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Exceptional cancellation review could not be started.",
      );
    } finally {
      setExceptionalCancellationSaving(false);
    }
  }

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

  async function authorizeException(): Promise<void> {
    const parsedWindow = returnWindowOverride.trim() === ""
      ? null
      : Number.parseInt(returnWindowOverride, 10);
    if (
      parsedWindow !== null
      && (
        !Number.isInteger(parsedWindow)
        || parsedWindow < 1
        || parsedWindow > 3650
      )
    ) {
      setError("Return-window override must be between 1 and 3650 days.");
      return;
    }

    const parsedRestocking = restockingPercentOverride.trim() === ""
      ? null
      : Number.parseFloat(restockingPercentOverride);
    if (
      parsedRestocking !== null
      && (
        Number.isNaN(parsedRestocking)
        || parsedRestocking < 0
        || parsedRestocking > 100
      )
    ) {
      setError("Restocking override must be between 0% and 100%.");
      return;
    }

    if (exceptionReason.trim() === "") {
      setError("A reason is required for a return-policy exception.");
      return;
    }

    if (
      parsedWindow === null
      && parsedRestocking === null
      && returnShippingOverride === ""
      && outboundShippingOverride === ""
    ) {
      setError("Select at least one return-policy term to override.");
      return;
    }

    setExceptionSaving(true);
    setError(null);

    try {
      const updated = await authorizeReturnPolicyException(
        order.id,
        {
          reason: exceptionReason.trim(),
          return_window_days_override: parsedWindow,
          restocking_fee_basis_points_override:
            parsedRestocking === null
              ? null
              : Math.round(parsedRestocking * 100),
          customer_pays_return_shipping_override:
            returnShippingOverride === ""
              ? null
              : returnShippingOverride === "customer",
          refund_outbound_shipping_override:
            outboundShippingOverride === ""
              ? null
              : outboundShippingOverride === "refund",
        },
      );
      onUpdated(updated);
      setExceptionReason("");
      setReturnWindowOverride("");
      setRestockingPercentOverride("");
      setReturnShippingOverride("");
      setOutboundShippingOverride("");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Return-policy exception could not be authorized.",
      );
    } finally {
      setExceptionSaving(false);
    }
  }

  async function confirmOrder(): Promise<void> {
    setConfirmationSaving(true);
    setError(null);

    try {
      const updated = await sendOrderConfirmation(order.id);
      onUpdated(updated);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Order confirmation could not be sent.",
      );
    } finally {
      setConfirmationSaving(false);
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
          <strong>Customer status:</strong>{" "}
          {customerStatusLabel(order.customer_status)}
        </span>
      </div>

      <div className="order-cancellation-operations order-confirmation-operations">
        <div>
          <strong>Customer confirmation</strong>
          <span>
            {order.order_confirmation.status === "sent"
              ? `Order Confirmed sent${
                  order.order_confirmation.sent_at !== null
                    ? ` · ${new Date(order.order_confirmation.sent_at).toLocaleString()}`
                    : ""
                }`
              : order.order_confirmation.status === "not_sent"
                ? "Not sent"
                : `Last attempt: ${order.order_confirmation.status}`}
          </span>
        </div>

        <p className="account-muted">
          Supplier Confirmed changes the order lifecycle but does not email the customer.
          After staff reviews the order, send the separate customer-facing “Order Confirmed” message here.
        </p>

        {order.order_confirmation.error_summary !== null
          && order.order_confirmation.status !== "sent" ? (
          <p className="account-muted">
            Last delivery result: {order.order_confirmation.error_summary}
          </p>
        ) : null}

        {order.order_confirmation.status !== "sent"
          && order.fulfillment_status !== "not_started"
          && order.customer_status !== "cancelled"
          && order.customer_status !== "refunded" ? (
          <button
            type="button"
            className="secondary-button"
            disabled={confirmationSaving}
            onClick={() => {
              void confirmOrder();
            }}
          >
            {confirmationSaving
              ? "Sending…"
              : order.order_confirmation.status === "not_sent"
                ? "Send Order Confirmed"
                : "Retry Order Confirmed"}
          </button>
        ) : null}

        {order.order_confirmation.status === "not_sent"
          && order.fulfillment_status === "not_started" ? (
          <small>Available after Supplier Confirmed is recorded.</small>
        ) : null}
      </div>

      <div className="order-cancellation-operations">
        <div>
          <strong>Cancellation</strong>
          <span>
            {order.cancellation === null
              ? order.cancellation_mode === "unrestricted"
                ? "No request · online cancellation open until Supplier Confirmed"
                : "No request · online cancellation closed after Supplier Confirmed"
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

        {order.cancellation === null
          && order.cancellation_mode === "closed_after_supplier_confirmation"
          && canManageCancellationExceptions ? (
          <details className="operations-policy-exception">
            <summary>Start exceptional cancellation review</summary>
            <p className="account-muted">
              Supplier Confirmed closes the normal customer cancellation path.
              Use this only to record an authorized case-by-case exception for review.
            </p>
            <label className="operations-field">
              <span>Exception reason</span>
              <textarea
                rows={3}
                maxLength={4000}
                value={exceptionalCancellationReason}
                onChange={(event) => {
                  setExceptionalCancellationReason(event.target.value);
                }}
              />
            </label>
            <button
              type="button"
              className="secondary-button"
              disabled={exceptionalCancellationSaving}
              onClick={() => {
                void startExceptionalCancellationReview();
              }}
            >
              {exceptionalCancellationSaving
                ? "Saving…"
                : "Start review"}
            </button>
          </details>
        ) : null}

        {order.cancellation?.status === "requested"
          && canManageCancellationExceptions ? (
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

      <div className="order-cancellation-operations">
        <div>
          <strong>Return policy</strong>
          <span>
            {order.refund_policy_snapshot === null
              ? "No snapshotted Refund Policy"
              : `Version ${order.refund_policy_snapshot.version}`}
          </span>
        </div>

        {order.refund_policy_snapshot?.refund_terms !== null
          && order.refund_policy_snapshot?.refund_terms !== undefined ? (
          <p className="account-muted">
            {order.refund_policy_snapshot.refund_terms.return_window_days === null
              ? "Case-by-case return eligibility"
              : `${order.refund_policy_snapshot.refund_terms.return_window_days}-day return window`}
            {" · "}
            {order.refund_policy_snapshot.refund_terms.restocking_fee_basis_points === null
              ? "Case-by-case restocking"
              : `${(
                  order.refund_policy_snapshot.refund_terms.restocking_fee_basis_points / 100
                ).toFixed(2)}% restocking`}
          </p>
        ) : null}

        {order.return_policy_exceptions.length > 0 ? (
          <div className="operations-policy-history">
            {order.return_policy_exceptions.map((exception) => (
              <div key={exception.id}>
                <strong>
                  Authorized exception · policy {exception.policy_version}
                </strong>
                <span>{exception.reason}</span>
                <small>
                  {exception.return_window_days_override !== null
                    ? `Return window: ${exception.return_window_days_override} days. `
                    : ""}
                  {exception.restocking_fee_basis_points_override !== null
                    ? `Restocking: ${(
                        exception.restocking_fee_basis_points_override / 100
                      ).toFixed(2)}%. `
                    : ""}
                  {exception.customer_pays_return_shipping_override !== null
                    ? (
                        exception.customer_pays_return_shipping_override
                          ? "Customer pays return shipping. "
                          : "Business pays return shipping. "
                      )
                    : ""}
                  {exception.refund_outbound_shipping_override !== null
                    ? (
                        exception.refund_outbound_shipping_override
                          ? "Outbound shipping refundable."
                          : "Outbound shipping non-refundable."
                      )
                    : ""}
                </small>
              </div>
            ))}
          </div>
        ) : (
          <p className="account-muted">
            No order-specific return-policy exceptions are recorded.
          </p>
        )}

        {canAuthorizeReturnException
          && order.refund_policy_snapshot !== null ? (
          <details>
            <summary>Authorize return-policy exception</summary>

            <label className="operations-field">
              <span>Return window override (days, optional)</span>
              <input
                type="number"
                min="1"
                max="3650"
                value={returnWindowOverride}
                onChange={(event) => {
                  setReturnWindowOverride(event.target.value);
                }}
              />
            </label>

            <label className="operations-field">
              <span>Restocking percentage override (optional)</span>
              <input
                type="number"
                min="0"
                max="100"
                step="0.01"
                value={restockingPercentOverride}
                onChange={(event) => {
                  setRestockingPercentOverride(event.target.value);
                }}
              />
            </label>

            <label className="operations-field">
              <span>Return shipping override</span>
              <select
                value={returnShippingOverride}
                onChange={(event) => {
                  setReturnShippingOverride(
                    event.target.value as "" | "customer" | "business",
                  );
                }}
              >
                <option value="">No override</option>
                <option value="customer">Customer pays</option>
                <option value="business">Business pays</option>
              </select>
            </label>

            <label className="operations-field">
              <span>Outbound shipping refund override</span>
              <select
                value={outboundShippingOverride}
                onChange={(event) => {
                  setOutboundShippingOverride(
                    event.target.value as "" | "nonrefundable" | "refund",
                  );
                }}
              >
                <option value="">No override</option>
                <option value="nonrefundable">Non-refundable</option>
                <option value="refund">Refund outbound shipping</option>
              </select>
            </label>

            <label className="operations-field">
              <span>Exception reason</span>
              <textarea
                rows={3}
                maxLength={4000}
                value={exceptionReason}
                onChange={(event) => {
                  setExceptionReason(event.target.value);
                }}
              />
            </label>

            <button
              type="button"
              className="secondary-button"
              disabled={exceptionSaving}
              onClick={() => {
                void authorizeException();
              }}
            >
              {exceptionSaving ? "Saving…" : "Authorize exception"}
            </button>
          </details>
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
          <span>Supplier reference (optional)</span>
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
        && order.fulfillment_status === "not_started"
        && !supplierOrderingBlocked ? (
        <p className="account-muted">
          Marking Supplier Confirmed is the customer-facing confirmation boundary
          and closes normal online cancellation requests for this order.
        </p>
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
            : nextStatus === "supplier_ordered"
              ? "Mark Supplier Confirmed"
              : `Mark ${label(nextStatus)}`}
        </button>
      ) : null}
    </div>
  );
}
