/**
 * Equipment-only sales and installation boundary.
 * Used by every product detail page. Keep the wording in one place.
 */
export function InstallationServicesNotice() {
  return (
    <aside
      className="catalog-purchase-boundary"
      aria-label="Installation and services"
    >
      <strong>Equipment only</strong>
      <p>
        Installation is arranged separately and is not included in this purchase
        or quote. Installation services and installer referrals may be available
        in the future; contact us to talk through your plans.
      </p>
    </aside>
  );
}
