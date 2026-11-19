// Overview workspace of Operations: the "Needs you" work list
// (../NeedsYouList.tsx), summary counts, readiness snapshot with launch
// dependency evidence, observed request patterns, and launch policies
// (../PolicyManagementPanel.tsx).
//
// Everything shown here is loaded by OperationsPage, which also handles the
// shortcuts (opening a request, conversation, order or metric switches
// workspace and scrolls to it).
//
// API: getOperationsSummary, getOperationsLaunchReadiness,
//   getOperationsSalesInsights in api/operations.ts -> /api/operations/summary,
//   /launch-readiness, /sales-insights
// Styles: .operations-metric*, .operations-readiness*, .operations-needs-you*

import type {
  OperationsCommunication,
  OperationsCommunicationThread,
  OperationsLaunchReadiness,
  OperationsOrder,
  OperationsQuote,
  OperationsSalesInsights,
  OperationsSummary,
} from "../../../api/operations";
import { LaunchDependencyEvidencePanel } from "../LaunchDependencyEvidencePanel";
import { NeedsYouList } from "../NeedsYouList";
import { PolicyManagementPanel } from "../PolicyManagementPanel";

/** Summary tiles; each opens the matching workspace. */
export type OperationsMetric =
  | "new_quotes"
  | "open_quotes"
  | "human_review"
  | "lab_testing"
  | "active_products"
  | "email_failures";

type OverviewWorkspaceProps = {
  hidden: boolean;
  roles: string[];
  summary: OperationsSummary | null;
  launchReadiness: OperationsLaunchReadiness | null;
  salesInsights: OperationsSalesInsights | null;
  quotes: OperationsQuote[];
  orders: OperationsOrder[];
  awaitingReplyThreads: OperationsCommunicationThread[];
  failedDeliveries: OperationsCommunication[];
  onOpenMetric: (metric: OperationsMetric) => void;
  onOpenRequest: (quoteId: string) => void;
  onOpenThread: (threadId: string) => void;
  onOpenOrder: (orderId: string) => void;
  onOpenDeliveryIssues: () => void;
  onPoliciesChanged: () => void;
};

export function OverviewWorkspace({
  hidden,
  roles,
  summary,
  launchReadiness,
  salesInsights,
  quotes,
  orders,
  awaitingReplyThreads,
  failedDeliveries,
  onOpenMetric,
  onOpenRequest,
  onOpenThread,
  onOpenOrder,
  onOpenDeliveryIssues,
  onPoliciesChanged,
}: OverviewWorkspaceProps) {
  return (
    <section
      id="operations-panel-overview"
      className="operations-workspace-panel"
      aria-label="Overview"
      hidden={hidden}
    >
    <NeedsYouList
      quotes={quotes}
      orders={orders}
      awaitingReplyThreads={awaitingReplyThreads}
      failedDeliveryCount={failedDeliveries.length}
      latestFailedDeliveryAt={
        failedDeliveries.reduce<string | null>(
          (latest, delivery) =>
            latest === null || delivery.created_at > latest
              ? delivery.created_at
              : latest,
          null,
        )
      }
      onOpenRequest={onOpenRequest}
      onOpenThread={onOpenThread}
      onOpenOrder={onOpenOrder}
      onOpenDeliveryIssues={onOpenDeliveryIssues}
    />

    {summary !== null ? (
      <section
        className="operations-metrics"
        aria-label="Operations summary"
      >
        {[
          ["new_quotes", summary.new_quotes, "New quotes"],
          ["open_quotes", summary.open_quotes, "Open quotes"],
          [
            "human_review",
            summary.recommendation_human_review,
            "Human review",
          ],
          [
            "lab_testing",
            summary.recommendation_lab_testing,
            "Lab testing",
          ],
          ["active_products", summary.active_products, "Active systems"],
          [
            "email_failures",
            summary.failed_email_deliveries,
            "Email failures",
          ],
        ].map(([metric, value, label]) => (
          <button
            key={metric}
            type="button"
            className="operations-metric"
            onClick={() => {
              onOpenMetric(metric as OperationsMetric);
            }}
            aria-label={`${label}: ${value}. Open relevant operations area.`}
          >
            <strong>{value}</strong>
            <span>{label}</span>
            <small>Open</small>
          </button>
        ))}
      </section>
    ) : null}

    {launchReadiness !== null ? (
      <details
        id="launch-readiness"
        className="operations-section operations-disclosure"
      >
        <summary className="operations-disclosure-summary">
          <span>
            <strong>Commercial launch</strong>
            <small>Readiness snapshot</small>
          </span>
        </summary>
        <div className="operations-disclosure-content">
          <section
            className="operations-sales-insights"
            aria-labelledby="launch-readiness-title"
          >
        <div className="operations-section-heading compact">
          <p className="eyebrow">Commercial launch</p>
          <h2 id="launch-readiness-title">Readiness snapshot</h2>
          <p>
            Read-only launch audit plus an enforced commerce phase gate.
            Changing launch phase is a deployment configuration action; this
            screen never bypasses tax, payment, or other checkout guards.
          </p>
        </div>

        <div className="operations-insight-lists">
          <div>
            <strong>Commerce launch gate</strong>
            <p>
              {launchReadiness.commerce_checkout_allowed ? "Open" : "Closed"}
              {" · "}
              {launchReadiness.launch_phase_label}
            </p>
            <small>
              {launchReadiness.commerce_gate_detail}
              {launchReadiness.commerce_blockers.length > 0
                ? ` Blockers: ${launchReadiness.commerce_blockers.join(" · ")}`
                : ""}
            </small>
          </div>
        </div>

        <div className="operations-insight-grid">
          <div>
            <strong>{launchReadiness.ready_count}</strong>
            <span>Ready</span>
            <small>Configured launch dependencies</small>
          </div>
          <div>
            <strong>{launchReadiness.action_required_count}</strong>
            <span>Action required</span>
            <small>Configuration or business input still needed</small>
          </div>
          <div>
            <strong>{launchReadiness.deferred_count}</strong>
            <span>Deferred</span>
            <small>Intentionally not commissioned yet</small>
          </div>
        </div>

        <div className="operations-insight-lists">
          {launchReadiness.checks.map((check) => (
            <div key={check.key}>
              <strong>{check.label}</strong>
              <p>
                {check.status === "ready"
                  ? "Ready"
                  : check.status === "action_required"
                    ? "Action required"
                    : "Deferred"}
                {" · "}
                {check.detail}
              </p>
              <small>
                {check.evidence.join(" · ")}
              </small>
            </div>
          ))}
        </div>

        <LaunchDependencyEvidencePanel roles={roles} />

        <p>
          Evaluated{" "}
          {new Date(launchReadiness.evaluated_at).toLocaleString()}.
        </p>
          </section>
        </div>
      </details>
    ) : null}

    {salesInsights !== null ? (
      <details
        id="assisted-sales-insights"
        className="operations-section operations-disclosure"
      >
        <summary className="operations-disclosure-summary">
          <span>
            <strong>Assisted sales</strong>
            <small>Observed request patterns</small>
          </span>
        </summary>
        <div className="operations-disclosure-content">
          <section
            className="operations-sales-insights"
            aria-labelledby="assisted-sales-insights-title"
          >
        <div className="operations-section-heading compact">
          <p className="eyebrow">Assisted sales</p>
          <h2 id="assisted-sales-insights-title">Observed request patterns</h2>
          <p>
            Read-only aggregates from structured customer requests. These
            observations do not change recommendation policy or unlock
            self-service purchasing.
          </p>
        </div>
        <div className="operations-insight-grid">
          <div>
            <strong>{salesInsights.structured_requests}</strong>
            <span>Structured requests</span>
            <small>{salesInsights.total_requests} total requests</small>
          </div>
          <div>
            <strong>{salesInsights.lab_required_requests}</strong>
            <span>Lab review required</span>
            <small>Well-water decision snapshot</small>
          </div>
          <div>
            <strong>{salesInsights.limited_utility_requests}</strong>
            <span>Limited utilities</span>
            <small>Power or drain reported unavailable</small>
          </div>
          <div>
            <strong>{salesInsights.known_hardness_requests}</strong>
            <span>Hardness value supplied</span>
            <small>Customer-provided structured context</small>
          </div>
          <div>
            <strong>{salesInsights.research_network_yes}</strong>
            <span>Filtration network signal</span>
            <small>Research-only; excluded from technical suitability</small>
          </div>
        </div>
        <div className="operations-insight-lists">
          <div>
            <strong>Source water</strong>
            <p>{salesInsights.source_water.map((item) => `${item.value}: ${item.count}`).join(" · ") || "No structured data yet"}</p>
          </div>
          <div>
            <strong>Treatment preference</strong>
            <p>{salesInsights.treatment_preference.map((item) => `${item.value}: ${item.count}`).join(" · ") || "No structured data yet"}</p>
          </div>
          <div>
            <strong>Top service ZIPs</strong>
            <p>{salesInsights.service_postal_codes.map((item) => `${item.value}: ${item.count}`).join(" · ") || "No ZIP data yet"}</p>
          </div>
        </div>
          </section>
        </div>
      </details>
    ) : null}

    <details
      id="launch-policies"
      className="operations-section operations-disclosure"
    >
      <summary className="operations-disclosure-summary">
        <span>
          <strong>Launch policies</strong>
          <small>Approved customer terms and policy versions</small>
        </span>
      </summary>
      <div className="operations-disclosure-content">
        <PolicyManagementPanel
          roles={roles}
          onPoliciesChanged={onPoliciesChanged}
        />
      </div>
    </details>

    </section>
  );
}
