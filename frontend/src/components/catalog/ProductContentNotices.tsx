/** PT54-G2: editorial copy only. Never alter product pricing or hardware selection. */
import notices from "./productNotices.json";
import "./ProductContentNotices.css";

/** Displayed once beneath the gallery of every product detail page, including Origin. */
export function ProductImageNotice() {
  return (
    <aside className="product-content-notice product-content-notice--image" aria-label="Product image disclaimer">
      <p>{notices.product_image_disclaimer}</p>
    </aside>
  );
}

/** Displayed once on the Harmony detail page, alongside the PureLine configurator. */
export function PureLineMaintenanceNotice() {
  return (
    <aside className="product-content-notice product-content-notice--maintenance" aria-label="PureLine maintenance notice">
      <p><strong>{notices.pureline_maintenance_heading}</strong>{" "}{notices.pureline_maintenance_body}</p>
    </aside>
  );
}
