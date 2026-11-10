import {
  useEffect,
  useState,
} from "react";

import {
  getPublicPolicy,
  type PolicyKind,
  type PublicPolicy,
} from "../api/policies";

type PolicyStatusPageProps = {
  kind: "privacy" | "terms";
  onNavigate: (path: string) => void;
};

const COMMERCIAL_POLICY_KINDS: PolicyKind[] = [
  "terms",
  "shipping",
  "cancellation",
  "refund",
  "warranty",
];

export function PolicyStatusPage({
  kind,
  onNavigate,
}: PolicyStatusPageProps) {
  const [policies, setPolicies] =
    useState<PublicPolicy[]>([]);
  const [loading, setLoading] =
    useState(true);
  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const requestedKinds: PolicyKind[] =
      kind === "privacy"
        ? ["privacy"]
        : COMMERCIAL_POLICY_KINDS;

    setLoading(true);

    void Promise.all(
      requestedKinds.map((policyKind) =>
        getPublicPolicy(policyKind),
      ),
    )
      .then((results) => {
        if (!cancelled) {
          setPolicies(results);
          setError(null);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(
            caught instanceof Error
              ? caught.message
              : "Policy status is unavailable.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [kind]);

  const privacy = kind === "privacy";
  const allApproved =
    policies.length > 0
    && policies.every((policy) => policy.approved);

  return (
    <main
      id="main-content"
      tabIndex={-1}
      className="detail-shell policy-status-page"
    >
      <button
        type="button"
        className="text-button"
        onClick={() => onNavigate("/")}
      >
        ← Home
      </button>

      <p className="eyebrow">
        {allApproved
          ? "Published policies"
          : "Policies"}
      </p>

      <h1>
        {privacy
          ? "Privacy"
          : "Terms & Policies"}
      </h1>

      {error !== null ? (
        <p role="alert">{error}</p>
      ) : loading ? (
        <p role="status">Loading policies…</p>
      ) : (
        <div className="policy-version-list">
          {policies.map((policy) => (
            <section key={policy.kind} className="policy-version-section">
              <h2>{policy.title}</h2>

              {policy.approved && policy.body !== null ? (
                <>
                  <p className="policy-status-lead">
                    Version {policy.version}
                    {policy.effective_at !== null
                      ? ` · Effective ${new Date(
                          policy.effective_at,
                        ).toLocaleDateString()}`
                      : ""}
                  </p>

                  <div className="policy-approved-body">
                    {policy.body}
                  </div>
                </>
              ) : (
                <>
                  <p className="policy-status-lead">
                    This policy is being finalized and is not yet published.
                  </p>

                  <p>
                    It will appear here once it has been approved.
                  </p>
                </>
              )}
            </section>
          ))}
        </div>
      )}

      {!allApproved && !loading && error === null ? (
        <p className="policy-status-note">
          The terms that apply to your purchase are included with your
          formal quote, for you to review before you approve it.
        </p>
      ) : null}
    </main>
  );
}
