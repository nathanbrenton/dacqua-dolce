// Static ownership checklist on the account page.



type MaintenanceChecksSectionProps = {
};

export function MaintenanceChecksSection({

}: MaintenanceChecksSectionProps) {
  return (
    <section className="account-panel account-maintenance-panel">
      <p className="eyebrow">Maintenance &amp; support</p>
      <h2>Useful ownership checks.</h2>
      <div className="account-maintenance-list">
        <article>
          <strong>Exterior water routing</strong>
          <p>Exterior irrigation, hose-bib, and pool-fill lines should generally bypass whole-property treatment when practical. Large pool-fill volumes can shorten filtration-media service life. Final routing still depends on the property and installation.</p>
        </article>
        <article>
          <strong>Softener salt</strong>
          <p>Inspect brine-tank salt about monthly and replenish it as needed. Follow the applicable manufacturer instructions; numeric minimum-fill guidance remains subject to manufacturer confirmation.</p>
        </article>
        <article>
          <strong>After a power interruption</strong>
          <p>Where applicable, verify the valve time-of-day on conventional softeners and backwashing carbon filters.</p>
        </article>
        <article>
          <strong>Replaceable cartridges</strong>
          <p>Plan on replacement about every six months where applicable, with actual life affected by water quality, use, micron rating, and system conditions. Follow a pressure or clog gauge when equipped.</p>
        </article>
      </div>
    </section>
  );
}
