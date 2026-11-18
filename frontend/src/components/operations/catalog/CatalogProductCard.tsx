// One product in the Catalog workspace: a collapsible card with the product's
// read-only facts (family, governance badges, warranty, specifications,
// claims) and its editors, each in its own file in this folder:
//   ProductRelationships      options, accessories & consumables
//   ProductPricingFields      pricing policy and promotions
//   ProductTaxFields          Stripe Tax classification
//   ProductAvailabilityFields lifecycle, exceptions and inventory
// Each editor keeps its own draft, which survives switching workspaces
// because Operations keeps every workspace mounted.

import { type OperationsProduct } from "../../../api/operations";
import { type OperationsNoticeProps } from "../operationsShared";
import {
  INVENTORY_STATUS_LABELS,
  PRICING_MODE_LABELS,
  PRODUCT_LIFECYCLE_LABELS,
} from "./catalogConstants";
import { ProductAvailabilityFields } from "./ProductAvailabilityFields";
import { ProductPricingFields } from "./ProductPricingFields";
import { ProductRelationships } from "./ProductRelationships";
import { ProductTaxFields } from "./ProductTaxFields";

type CatalogProductCardProps = {
  product: OperationsProduct;
  /** Every catalog product, for choosing related products. */
  products: OperationsProduct[];
  privileged: boolean;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onProductChange: (product: OperationsProduct) => void;
  onInventorySaved: () => void;
} & OperationsNoticeProps;

export function CatalogProductCard({
  product,
  products,
  privileged,
  open,
  onOpenChange,
  onProductChange,
  onInventorySaved,
  onMessage,
  onError,
}: CatalogProductCardProps) {
  const sectionProps = {
    product,
    privileged,
    onProductChange,
    onMessage,
    onError,
  };

  return (
    <details
      className="operations-product operations-product-disclosure"
      open={open}
      onToggle={(event) => {
        onOpenChange(event.currentTarget.open);
      }}
    >
      <summary className="operations-product-disclosure-summary">
        <span
          className="operations-product-disclosure-chevron"
          aria-hidden="true"
        />
        <span className="operations-product-disclosure-identity">
          <span className="product-meta">
            {product.manufacturer}
            {" · "}
            {product.category}
          </span>
          <strong>{product.name}</strong>
          <code>{product.sku}</code>
        </span>
        <span className="operations-product-disclosure-status">
          <span>
            Lifecycle: {PRODUCT_LIFECYCLE_LABELS[product.lifecycle_status]
              ?? product.lifecycle_status}
          </span>
          <span>
            Inventory: {INVENTORY_STATUS_LABELS[product.inventory.status]
              ?? product.inventory.status}
          </span>
          <span>
            Pricing: {PRICING_MODE_LABELS[product.pricing.mode]
              ?? product.pricing.mode}
          </span>
        </span>
      </summary>

      <div className="operations-product-disclosure-content">
      <header>
        <p className="product-meta">
          {product.manufacturer}
          {" · "}
          {product.category}
        </p>
        <h3>{product.name}</h3>
        <code>{product.sku}</code>

        <div className="operations-catalog-architecture">
          <span>
            <strong>Family</strong>
            {product.product_family ?? "Not assigned"}
          </span>
          <span>
            <strong>System</strong>
            {product.system_type ?? "Not assigned"}
          </span>
          <span>
            <strong>Active configurations</strong>
            {product.active_variant_count}
          </span>
          <span>
            <strong>Public options</strong>
            {product.public_option_count}
          </span>
        </div>

        <div className="operations-governance-badges">
          <span>
            Pricing: {PRICING_MODE_LABELS[product.pricing.mode] ?? product.pricing.mode}
          </span>
          <span>
            Lifecycle: {PRODUCT_LIFECYCLE_LABELS[product.lifecycle_status] ?? product.lifecycle_status}
          </span>
          <span>
            Inventory: {INVENTORY_STATUS_LABELS[product.inventory.status] ?? product.inventory.status}
          </span>
          <span>Reserved: {product.inventory.quantity_reserved}</span>
          <span>
            Employee review: {product.assisted_sale_required ? "required" : "not required"}
          </span>
          <span>
            Online sale: {product.online_sale_approved ? "approved" : "blocked"}
          </span>
          <span>
            Warranty docs: {product.warranty_documents.filter((document) => document.active && document.public && document.verified_at !== null && document.checksum_sha256 !== null).length} verified public
          </span>
          <span>
            Specifications: {product.specifications.filter((specification) => specification.active && specification.public && specification.verified_at !== null).length} verified public
          </span>
          <span>
            Manufacturer claims: {product.manufacturer_claims.filter((claim) => claim.public_ready).length} publishable
          </span>
        </div>

        {product.assisted_sale_required ? (
          <p className="operations-note">
            Assisted sale: employee review is required before purchase.
          </p>
        ) : null}

        {!product.online_sale_approved ? (
          <p className="operations-note">
            Online sale remains blocked pending applicable manufacturer/component policy verification.
          </p>
        ) : null}
        {product.warranty_documents.length > 0 ? (
          <details className="operations-product-relationships">
            <summary>Manufacturer warranty documents</summary>
            <div className="operations-product-relationship-list">
              {product.warranty_documents.map((document) => (
                <div key={document.id} className="operations-product-relationship">
                  <div>
                    <strong>{document.title}</strong>
                    <code>v{document.version}</code>
                    <span>
                      {document.verified_at !== null ? "verified" : "review required"}
                      {document.public ? " · public" : " · internal"}
                      {document.active ? " · active" : " · retired"}
                    </span>
                    {document.source_reference !== null ? (
                      <small>Source: {document.source_reference}</small>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          </details>
        ) : (
          <p className="operations-note">
            No manufacturer warranty document has been recorded for this product.
          </p>
        )}

        {product.specifications.length > 0 ? (
          <details className="operations-product-relationships">
            <summary>Specification provenance</summary>
            <div className="operations-product-relationship-list">
              {product.specifications.map((specification) => (
                <div key={specification.id} className="operations-product-relationship">
                  <div>
                    <strong>{specification.label}</strong>
                    <span>
                      {specification.value_text}
                      {specification.unit !== null ? ` ${specification.unit}` : ""}
                    </span>
                    <span>
                      {specification.verified_at !== null ? "verified" : "review required"}
                      {specification.public ? " · public" : " · internal"}
                      {specification.active ? " · active" : " · retired"}
                    </span>
                    <small>Source: {specification.source_reference}</small>
                  </div>
                </div>
              ))}
            </div>
          </details>
        ) : null}

        {product.manufacturer_claims.length > 0 ? (
          <details className="operations-product-relationships">
            <summary>Manufacturer-stated claims</summary>
            <div className="operations-product-relationship-list">
              {product.manufacturer_claims.map((claim) => (
                <div key={claim.id} className="operations-product-relationship">
                  <div>
                    <strong>{claim.claim_text}</strong>
                    <span>
                      {claim.public_ready ? "publishable as Manufacturer-stated" : "not publishable"}
                      {claim.active ? " · active" : " · retired"}
                    </span>
                    <small>Source: {claim.source_reference}</small>
                    {claim.approved_at !== null ? (
                      <small>Approved: {new Date(claim.approved_at).toLocaleString()}</small>
                    ) : null}
                    {claim.expires_at !== null ? (
                      <small>Expires: {new Date(claim.expires_at).toLocaleString()}</small>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          </details>
        ) : (
          <p className="operations-note">
            No manufacturer-stated claims are recorded for this product. Unsupported performance or capacity claims remain suppressed.
          </p>
        )}
      </header>

      <ProductRelationships products={products} {...sectionProps} />

      <div className="operations-product-grid">
        <ProductPricingFields {...sectionProps} />
        <ProductTaxFields {...sectionProps} />
        <ProductAvailabilityFields
          onInventorySaved={onInventorySaved}
          {...sectionProps}
        />
      </div>
      </div>
    </details>
  );
}
