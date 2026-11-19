// Orders workspace of Operations: customer-linked order history, totals,
// delivery/billing addresses and manual fulfillment controls.
//
// The order list is loaded by OperationsPage (Overview's "Needs you" list and
// the Customers workspace use it too) and comes in as `orders`. The search box
// is controlled by the page so Overview shortcuts can clear it before scrolling
// to an order (#operations-order-<id>).
//
// Fulfillment edits: ../OrderFulfillmentControls.tsx (updateOrderFulfillment ->
//   /api/operations/orders/{id}/fulfillment). Next-step rules: ../operationsNextSteps.ts
// Styles: .operations-order* in styles.css

import { useMemo } from "react";

import type { CommercialAddress } from "../../../api/commercial";
import type { OperationsOrder } from "../../../api/operations";
import { formatUsPhoneInput } from "../../../utils/phone";
import { CopyEmailButton } from "../CopyEmailButton";
import { formatMoney } from "../operationsMoney";
import { OrderFulfillmentControls } from "../OrderFulfillmentControls";
import { exactEntryProps } from "../../forms/textEntry";

function commercialAddressLines(address: CommercialAddress): string[] {
  return [
    address.recipient_name,
    address.line1,
    address.line2,
    `${address.city}, ${address.region_code} ${address.postal_code}`,
    address.country_code,
    address.phone,
  ].filter((value): value is string => value !== null && value !== "");
}

type OrdersWorkspaceProps = {
  hidden: boolean;
  orders: OperationsOrder[];
  roles: string[];
  search: string;
  onSearchChange: (search: string) => void;
  onOrderChange: (order: OperationsOrder) => void;
};

export function OrdersWorkspace({
  hidden,
  orders,
  roles,
  search,
  onSearchChange,
  onOrderChange,
}: OrdersWorkspaceProps) {
  const filteredOrders = useMemo(() => {
    const query =
      search.trim().toLowerCase();

    if (query.length === 0) {
      return orders;
    }

    return orders.filter((order) => {
      const searchable = [
        order.id,
        order.status,
        order.fulfillment_status,
        order.supplier_order_reference ?? "",
        order.shipment?.carrier ?? "",
        order.shipment?.tracking_number ?? "",
        order.customer.email,
        order.customer.first_name ?? "",
        order.customer.last_name ?? "",
        order.customer.phone ?? "",
        ...order.items.flatMap((item) => [
          item.sku,
          item.name,
        ]),
      ]
        .join(" ")
        .toLowerCase();

      return searchable.includes(query);
    });
  }, [
    orders,
    search,
  ]);

  return (
    <section
      id="operations-panel-orders"
      className="operations-workspace-panel"
      aria-label="Customer orders"
      hidden={hidden}
    >
    <details
      id="order-history"
      className="operations-section operations-disclosure"
    >
      <summary className="operations-disclosure-summary">
        <span>
          <strong>Customer orders</strong>
          <small>Order history</small>
        </span>
      </summary>
      <div className="operations-disclosure-content">
      <div className="operations-section-heading">
        <p className="eyebrow">Order History</p>
        <h2>Customer orders</h2>
        <p>
          Customer-linked order history and manual fulfillment controls.
          Payment-provider details are not exposed.
        </p>
      </div>

      <label
        className={
          "operations-field "
          + "operations-customer-search"
        }
      >
        <span>Search orders</span>
        <input
          {...exactEntryProps}
          type="search"
          placeholder="Customer, email, order ID, SKU, status…"
          value={search}
          onChange={(event) => {
            onSearchChange(
              event.target.value,
            );
          }}
        />
      </label>

      {orders.length === 0 ? (
        <p className="account-muted">
          No customer orders recorded.
        </p>
      ) : filteredOrders.length === 0 ? (
        <p className="account-muted">
          No orders match this search.
        </p>
      ) : (
        <div className="operations-customer-list">
          {filteredOrders.map((order) => {
            const customerName = [
              order.customer.first_name,
              order.customer.last_name,
            ]
              .filter(
                (value): value is string =>
                  value !== null,
              )
              .join(" ");

            return (
              <article
                key={order.id}
                id={`operations-order-${order.id}`}
                className="operations-customer operations-order"
              >
                <header>
                  <div>
                    <p className="product-meta">
                      Customer status · {order.customer_status.replaceAll(
                        "_",
                        " ",
                      )}
                      {" · "}
                      payment {order.status}
                    </p>

                    <h3>
                      {customerName || order.customer.email}
                    </h3>

                    {customerName.length > 0 ? (
                      <p>
                        <CopyEmailButton email={order.customer.email} />
                      </p>
                    ) : null}

                    {order.customer.phone !== null ? (
                      <p>
                        <a
                          href={`tel:${order.customer.phone}`}
                        >
                          {formatUsPhoneInput(
                            order.customer.phone,
                          )}
                        </a>
                      </p>
                    ) : null}

                    <small>
                      {new Date(
                        order.created_at,
                      ).toLocaleString()}
                      {" · "}
                      {order.id}
                    </small>
                  </div>
                </header>

                <div className="operations-address-list">
                  {order.items.map((item, index) => (
                    <div
                      key={
                        `${order.id}-${item.sku}-${index}`
                      }
                      className="operations-address"
                    >
                      <strong>
                        {item.name}
                      </strong>

                      <address>
                        {item.sku}
                        <br />
                        {item.quantity} × {formatMoney(
                          item.unit_amount_minor,
                          item.currency,
                        )}
                      </address>

                      <small>
                        Line total: {formatMoney(
                          item.line_total_minor,
                          item.currency,
                        )}
                        {item.estimated_lead_time !== null ? (
                          <>
                            <br />
                            Estimated lead time:{" "}
                            {item.estimated_lead_time}
                          </>
                        ) : null}
                      </small>
                    </div>
                  ))}

                  <div className="operations-address">
                    <strong>Commercial total</strong>

                    <address>
                      Products: {formatMoney(
                        order.subtotal_amount_minor,
                        order.currency,
                      )}
                      {order.charges.map((charge, index) => (
                        <span key={`${order.id}-${charge.kind}-${index}`}>
                          <br />
                          {charge.label}: {formatMoney(
                            charge.amount_minor,
                            order.currency,
                          )}
                        </span>
                      ))}
                      <br />
                      <strong>
                        Final total: {formatMoney(
                          order.total_amount_minor,
                          order.currency,
                        )}
                      </strong>
                    </address>

                    <small>
                      Payment state remains separate from fulfillment.
                    </small>
                  </div>

                  {order.delivery_address !== null ? (
                    <div className="operations-address">
                      <strong>Delivery / service snapshot</strong>
                      <address>
                        {commercialAddressLines(order.delivery_address).map((line) => (
                          <span key={line}>{line}<br /></span>
                        ))}
                      </address>
                    </div>
                  ) : null}

                  {order.billing_address !== null ? (
                    <div className="operations-address">
                      <strong>Billing snapshot</strong>
                      <address>
                        {commercialAddressLines(order.billing_address).map((line) => (
                          <span key={line}>{line}<br /></span>
                        ))}
                      </address>
                    </div>
                  ) : null}
                </div>

                <OrderFulfillmentControls
                  order={order}
                  roles={roles}
                  onUpdated={(updated) => {
                    onOrderChange(updated);
                  }}
                />
              </article>
            );
          })}
        </div>
      )}
      </div>
    </details>

    </section>
  );
}
