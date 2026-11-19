// The customer's orders: stage, items, totals, delivery address, and
// cancellation requests.
//
// API: requestOrderCancellation in api/orders.ts

import {
  type Dispatch,
  type SetStateAction,
  useState,
} from "react";
import { type Order, requestOrderCancellation } from "../../../api/orders";
import {
  commercialAddressLines,
  money,
  orderStageLabel,
} from "../accountFormat";
import { type AccountNoticeProps } from "../accountShared";

type OrdersSectionProps = {
  orders: Order[];
  onOrdersChange: Dispatch<SetStateAction<Order[]>>;
} & AccountNoticeProps;

export function OrdersSection({
  orders,
  onOrdersChange: setOrders,
  onError: setError,
  onNotice: setSaveNotice,
}: OrdersSectionProps) {
  const [cancellationReasons, setCancellationReasons] =
    useState<Record<string, string>>({});
  const [cancellationBusyOrderId, setCancellationBusyOrderId] =
    useState<string | null>(null);

  async function submitOrderCancellation(
    order: Order,
  ): Promise<void> {
    setCancellationBusyOrderId(order.id);
    setError(null);
    setSaveNotice(null);

    try {
      const reason = cancellationReasons[order.id]?.trim() || null;
      const cancellation = await requestOrderCancellation(
        order.id,
        reason,
      );

      setOrders((current) =>
        current.map((candidate) =>
          candidate.id === order.id
            ? {
                ...candidate,
                cancellation,
              }
            : candidate,
        ),
      );
      setCancellationReasons((current) => {
        const next = { ...current };
        delete next[order.id];
        return next;
      });
      setSaveNotice(
        cancellation.status === "approved"
          ? "Cancellation accepted. Our team will complete any required payment or administrative steps."
          : "Cancellation review requested.",
      );
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Cancellation request failed.",
      );
    } finally {
      setCancellationBusyOrderId(null);
    }
  }

  return (
    <section className="account-panel">
      <h2>Orders</h2>

      {orders.length === 0 ? (
        <p className="account-muted">
          No orders yet.
        </p>
      ) : (
        <div className="order-list">
          {orders.map((order) => (
            <article
              key={order.id}
              className="order-row"
            >
              <div>
                <strong>
                  {orderStageLabel(order.customer_status)}
                </strong>
                <p>
                  {new Date(
                    order.created_at,
                  ).toLocaleDateString()}
                </p>

                <p className="account-muted">
                  {order.customer_status === "received"
                    ? "Your order has been received."
                    : order.customer_status === "processing"
                      ? "We are preparing the order and confirming supplier availability."
                      : order.customer_status === "supplier_confirmed"
                        ? "D’Acqua Dolce has confirmed the supplier stage for this order."
                        : order.customer_status === "awaiting_shipment"
                          ? "Your order is being prepared for shipment."
                          : order.customer_status === "shipped"
                            ? "Your order is on the way."
                            : order.customer_status === "completed"
                              ? "This order is complete."
                              : null}
                </p>

                {order.items.some(
                  (item) =>
                    item.estimated_lead_time !== null,
                ) ? (
                  <p className="account-muted">
                    Estimated lead time:{" "}
                    {order.items
                      .map(
                        (item) =>
                          item.estimated_lead_time,
                      )
                      .filter(
                        (value): value is string =>
                          value !== null,
                      )
                      .join(" · ")}
                  </p>
                ) : null}

                {order.shipment !== null ? (
                  <p className="account-muted">
                    Tracking:{" "}
                    {order.shipment.carrier}{" "}
                    {order.shipment.tracking_number}
                    {order.shipment.tracking_url !== null ? (
                      <>
                        {" · "}
                        <a
                          href={order.shipment.tracking_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Track shipment
                        </a>
                      </>
                    ) : null}
                  </p>
                ) : null}

                {order.cancellation !== null ? (
                  <div className="account-order-cancellation">
                    <strong>Cancellation</strong>
                    <p className="account-muted">
                      {order.cancellation.status === "requested"
                        ? "Cancellation review requested. Our team will review the supplier/order status."
                        : order.cancellation.status === "approved"
                          ? "Cancellation accepted. Any required payment reversal or administrative completion is handled separately."
                          : order.cancellation.status === "declined"
                            ? "Cancellation was reviewed and not approved. Contact us if you need help."
                            : "Cancellation workflow completed."}
                    </p>
                    {order.cancellation.reason !== null ? (
                      <p className="account-muted">
                        Reason: {order.cancellation.reason}
                      </p>
                    ) : null}
                  </div>
                ) : (
                  order.status !== "cancelled"
                  && order.status !== "refunded"
                ) ? (
                  <div className="account-order-cancellation">
                    <p className="account-muted">
                      {order.cancellation_mode === "unrestricted"
                        ? "Online cancellation is available until D’Acqua Dolce marks the order Supplier Confirmed."
                        : "Online cancellation is closed after Supplier Confirmed. Contact D’Acqua Dolce if exceptional review is needed."}
                    </p>
                    {order.cancellation_mode === "unrestricted" ? (
                      <>
                        <label className="account-order-cancellation-field">
                          <span>Reason (optional)</span>
                          <textarea
                            rows={2}
                            maxLength={2000}
                            value={cancellationReasons[order.id] ?? ""}
                            onChange={(event) => {
                              setCancellationReasons((current) => ({
                                ...current,
                                [order.id]: event.target.value,
                              }));
                            }}
                          />
                        </label>
                        <button
                          type="button"
                          className="account-action"
                          disabled={cancellationBusyOrderId === order.id}
                          onClick={() => {
                            void submitOrderCancellation(order);
                          }}
                        >
                          {cancellationBusyOrderId === order.id
                            ? "Submitting…"
                            : "Cancel order"}
                        </button>
                      </>
                    ) : null}
                  </div>
                ) : null}

                {order.charges.length > 0 ? (
                  <p className="account-muted">
                    Products {money(order.subtotal_amount_minor, order.currency)}
                    {order.charges.map((charge) => (
                      ` · ${charge.label} ${money(charge.amount_minor, order.currency)}`
                    )).join("")}
                  </p>
                ) : null}

                {order.delivery_address !== null ? (
                  <address className="account-order-address">
                    <strong>Delivery / service address</strong><br />
                    {commercialAddressLines(order.delivery_address).map((line) => (
                      <span key={line}>{line}<br /></span>
                    ))}
                  </address>
                ) : null}
              </div>

              <strong>
                {money(
                  order.total_amount_minor,
                  order.currency,
                )}
              </strong>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
