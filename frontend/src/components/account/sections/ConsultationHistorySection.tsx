// The customer's past quote and consultation requests.
//
// API: getCustomerRequests in api/account.ts

import { type CustomerRequestSummary } from "../../../api/account";

type ConsultationHistorySectionProps = {
  requests: CustomerRequestSummary[];
};

export function ConsultationHistorySection({
  requests: customerRequests,
}: ConsultationHistorySectionProps) {
  return (
    <section className="account-panel account-requests-panel">
      <p className="eyebrow">Requests</p>
      <h2>Your consultation history.</h2>
      {customerRequests.length === 0 ? (
        <p className="account-muted">No signed-in requests are attached to this account yet.</p>
      ) : (
        <div className="account-request-list">
          {customerRequests.map((request) => (
            <article key={request.id} className="account-request-row">
              <div>
                <strong>{request.product_name ?? request.recommendation_title ?? "Water treatment consultation"}</strong>
                <p>{new Date(request.created_at).toLocaleDateString()} · {request.status.replaceAll("_", " ")}</p>
              </div>
              <div className="account-request-badges">
                {request.requires_third_party_lab ? <span>Lab testing</span> : null}
                {request.human_review ? <span>Human review</span> : null}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
