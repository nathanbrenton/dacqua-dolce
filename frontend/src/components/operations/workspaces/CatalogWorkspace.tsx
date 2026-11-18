// Catalog workspace of Operations: product display order, Notify When in
// Stock demand, and one collapsible card per product (catalog/CatalogProductCard.tsx
// and the editor sections beside it).
//
// The product list itself is loaded by OperationsPage (other workspaces use it
// too) and comes in as `products`; saves hand the updated product back through
// onProductChange. Stock notifications are loaded here.
//
// API: getOperationsCatalog, getOperationsStockNotifications and the product
//   update calls in api/operations.ts -> /api/operations/catalog/...
// Styles: "Operations" catalog sections of styles.css (.operations-product*,
//   .operations-availability-demand)

import {
  useCallback,
  useEffect,
  useState,
} from "react";
import {
  type OperationsProduct,
  type OperationsStockNotification,
  getOperationsStockNotifications,
} from "../../../api/operations";
import { type OperationsNoticeProps } from "../operationsShared";
import { ProductFamilyOrderPanel } from "../ProductFamilyOrderPanel";
import { CatalogProductCard } from "../catalog/CatalogProductCard";

type CatalogWorkspaceProps = {
  hidden: boolean;
  products: OperationsProduct[];
  privileged: boolean;
  onProductChange: (product: OperationsProduct) => void;
} & OperationsNoticeProps;

export function CatalogWorkspace({
  hidden,
  products,
  privileged,
  onProductChange,
  onMessage,
  onError,
}: CatalogWorkspaceProps) {
  const [stockNotifications, setStockNotifications] =
    useState<OperationsStockNotification[]>([]);
  const [openCatalogProductId, setOpenCatalogProductId] =
    useState<string | null>(null);

  const refreshStockNotifications = useCallback(() => {
    void getOperationsStockNotifications()
      .then(setStockNotifications)
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    refreshStockNotifications();
  }, [refreshStockNotifications]);

  return (
    <section
      id="operations-panel-catalog"
      className="operations-workspace-panel"
      aria-label="Catalog governance"
      hidden={hidden}
    >
    <details
      id="catalog-governance"
      className="operations-section operations-disclosure"
    >
      <summary className="operations-disclosure-summary">
        <span>
          <strong>Pricing & inventory</strong>
          <small>Catalog governance</small>
        </span>
      </summary>

      <div className="operations-disclosure-content">

      <div className="operations-section-heading">
        <p className="eyebrow">Catalog Governance</p>
        <h2>Pricing &amp; inventory</h2>
        <p>
          Enter only authoritative business/manufacturer data.
          Restricted products should use a non-public pricing policy
          rather than a workaround.
        </p>
      </div>

      <ProductFamilyOrderPanel />

      <section
        className="operations-availability-demand"
        aria-labelledby="operations-availability-demand-heading"
      >
        <header>
          <div>
            <p className="operations-subsection-label">Availability demand</p>
            <h3 id="operations-availability-demand-heading">
              Notify When in Stock requests
            </h3>
          </div>
          <strong>
            {stockNotifications.length}{" "}
            {stockNotifications.length === 1
              ? "active request"
              : "active requests"}
          </strong>
        </header>

        <p>
          These requests are waiting for a one-time transactional availability
          notice. When authorized staff saves inventory as available, the app
          sends the notice automatically. Successful deliveries leave this
          active queue; failed or suppressed deliveries remain available for a
          later staff-confirmed retry.
        </p>

        {stockNotifications.length === 0 ? (
          <p className="operations-request-empty">
            No active Notify When in Stock requests.
          </p>
        ) : (
          <div className="operations-availability-demand-list">
            {stockNotifications.map((request) => (
              <article key={request.id}>
                <div>
                  <strong>{request.product_name}</strong>
                  <span>{request.product_sku}</span>
                </div>
                <a href={`mailto:${request.email}`}>{request.email}</a>
                <small>
                  Requested {new Date(request.created_at).toLocaleString()}
                </small>
              </article>
            ))}
          </div>
        )}
      </section>

      <div className="operations-product-list">
        {products.map((product) => (
          <CatalogProductCard
            key={product.id}
            product={product}
            products={products}
            privileged={privileged}
            open={openCatalogProductId === product.id}
            onOpenChange={(open) => {
              setOpenCatalogProductId((current) => {
                if (open) {
                  return product.id;
                }
                return current === product.id ? null : current;
              });
            }}
            onProductChange={onProductChange}
            onInventorySaved={refreshStockNotifications}
            onMessage={onMessage}
            onError={onError}
          />
        ))}
      </div>

      </div>
    </details>

    </section>
  );
}
