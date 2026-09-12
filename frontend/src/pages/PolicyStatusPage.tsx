type PolicyStatusPageProps = {
  kind: "privacy" | "terms";
  onNavigate: (path: string) => void;
};

export function PolicyStatusPage({
  kind,
  onNavigate,
}: PolicyStatusPageProps) {
  const privacy =
    kind === "privacy";

  return (
    <main className="detail-shell policy-status-page">
      <button
        type="button"
        className="text-button"
        onClick={() => onNavigate("/")}
      >
        ← Home
      </button>

      <p className="eyebrow">
        Pre-launch policy status
      </p>

      <h1>
        {privacy
          ? "Privacy"
          : "Terms & Policies"}
      </h1>

      {privacy ? (
        <>
          <p className="policy-status-lead">
            D&apos;Acqua Dolce is completing its
            privacy and data-governance review for
            public launch.
          </p>

          <p>
            This pre-launch page is not a final privacy
            policy. Final disclosures concerning data
            collection, retention and deletion,
            tracking, marketing consent, data sharing,
            and consumer privacy rights require
            business and legal approval.
          </p>
        </>
      ) : (
        <>
          <p className="policy-status-lead">
            D&apos;Acqua Dolce is completing its
            customer terms and operating policies for
            public launch.
          </p>

          <p>
            Final customer Terms, Shipping Policy,
            Subscription Terms, Cancellation Policy,
            Refund Policy, and Warranty language
            require business and legal approval. This
            page is not a final customer agreement.
          </p>
        </>
      )}

      <p className="policy-status-note">
        Final approved policy language will replace
        this pre-launch notice before the applicable
        production workflows are activated.
      </p>
    </main>
  );
}
