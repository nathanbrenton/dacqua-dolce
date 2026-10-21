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
      <strong>Installation &amp; Services</strong>
      <p>
        Equipment is currently offered without installation. Installation services
        and installer referrals may be available in the future. Please contact us
        to discuss your needs.
      </p>
    </aside>
  );
}
