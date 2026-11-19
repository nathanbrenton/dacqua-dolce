/**
 * Audit workspace: privileged activity history (developer role only).
 *
 * Data:    getOperationsAuditEvents() in src/api/operations.ts
 *          -> GET /api/operations/audit-events (backend/app/api/operations.py)
 * Styles:  .operations-audit-* in src/styles.css ("PT25 — Audit Log troubleshooting polish")
 * Tests:   backend/tests/test_operations_audit_events.py
 * Shown by OperationsPage.tsx only when the user has the developer role.
 * Loads the first page when its disclosure is first opened.
 */
import { useMemo, useState } from "react";

import {
  getOperationsAuditEvents,
  type OperationsAuditEvent,
  type OperationsAuditEventQuery,
} from "../../../api/operations";
import { localDateTimeValue } from "../operationsShared";
import { exactEntryProps } from "../../forms/textEntry";

const AUDIT_ACTION_LABELS: Record<string, string> = {
  "customer.equipment_recorded": "Installed equipment recorded",
  "customer.equipment_updated": "Installed equipment updated",
  "account.registered": "Account registered",
  "authentication.failed": "Authentication failed",
  "authentication.email_verification_issued": "Email verification issued",
  "authentication.email_verification_completed": "Email verification completed",
  "authentication.email_verification.failed": "Email verification failed",
  "authentication.logout": "Signed out",
  "authentication.session_revoked": "Session revoked",
  "cart.item_added": "Cart item added",
  "cart.item_removed": "Cart item removed",
  "catalog.family_order_changed": "Product display order changed",
  "catalog.inventory_changed": "Inventory changed",
  "catalog.pricing_changed": "Pricing policy changed",
  "catalog.relationship_created": "Product relationship created",
  "catalog.relationship_changed": "Product relationship changed",
  "catalog.relationship_removed": "Product relationship removed",
  "communications.reply_attempted": "Customer reply attempted",
  "communications.thread_status_changed": "Inbox thread status changed",
  "customer.address_created": "Customer address created",
  "customer.address_deleted": "Customer address deleted",
  "customer.profile_updated": "Customer profile updated",
  "identity.operations_roles_changed": "Operations roles changed",
  "order.status_changed": "Order status changed",
  "order.fulfillment_status_changed": "Fulfillment status changed",
  "order.shipment_recorded": "Shipment recorded",
  "quote.notes_updated": "Request notes updated",
  "quote.requested": "Customer request submitted",
  "quote.status_changed": "Request status changed",
  "formal_quote.created": "Formal quote created",
  "formal_quote.presented": "Formal quote presented",
  "formal_quote.approved": "Formal quote approved",
  "launch_dependency_evidence.updated": "Launch dependency evidence updated",
  "maintenance.reminder_delivery_attempted": "Maintenance reminder attempted",
};

const AUDIT_ENTITY_LABELS: Record<string, string> = {
  cart_item: "Cart item",
  communication_thread: "Communication thread",
  customer_address: "Customer address",
  customer_equipment: "Customer equipment",
  customer_profile: "Customer profile",
  order: "Order",
  product: "Product",
  product_family_order: "Product display order",
  product_relationship: "Product relationship",
  quote_request: "Customer request",
  formal_quote: "Formal quote",
  launch_dependency_evidence: "Launch dependency evidence",
  maintenance_reminder: "Maintenance reminder",
  user: "User account",
  user_session: "User session",
  email_verification: "Email verification",
};

function auditActionLabel(action: string): string {
  return AUDIT_ACTION_LABELS[action] ?? action.replaceAll("_", " ");
}

function auditEntityLabel(entityType: string): string {
  return AUDIT_ENTITY_LABELS[entityType] ?? entityType.replaceAll("_", " ");
}

type AuditFilterDraft = {
  search: string;
  fromLocal: string;
  toLocal: string;
  actor: string;
  outcome: "all" | "succeeded" | "failed";
  action: string;
  entityType: string;
  entityId: string;
  environment: string;
  requestId: string;
  sort: "newest" | "oldest";
};

const EMPTY_AUDIT_FILTERS: AuditFilterDraft = {
  search: "",
  fromLocal: "",
  toLocal: "",
  actor: "",
  outcome: "all",
  action: "",
  entityType: "",
  entityId: "",
  environment: "",
  requestId: "",
  sort: "newest",
};

function auditQueryFromDraft(
  draft: AuditFilterDraft,
): OperationsAuditEventQuery {
  const from = draft.fromLocal
    ? new Date(draft.fromLocal).toISOString()
    : undefined;
  const to = draft.toLocal
    ? new Date(draft.toLocal).toISOString()
    : undefined;

  return {
    from,
    to,
    actor: draft.actor.trim() || undefined,
    outcome: draft.outcome === "all"
      ? undefined
      : draft.outcome,
    action: draft.action.trim() || undefined,
    entity_type: draft.entityType.trim() || undefined,
    entity_id: draft.entityId.trim() || undefined,
    environment: draft.environment || undefined,
    request_id: draft.requestId.trim() || undefined,
    search: draft.search.trim() || undefined,
    sort: draft.sort,
    page_size: 50,
  };
}

function csvCell(value: string | null): string {
  const text = value ?? "";
  return `"${text.replaceAll('"', '""')}"`;
}

function CopyAuditValueButton({
  value,
  label = "Copy",
}: {
  value: string;
  label?: string;
}) {
  const [copied, setCopied] = useState(false);

  async function copyValue(): Promise<void> {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1400);
    } catch {
      setCopied(false);
    }
  }

  return (
    <button
      type="button"
      className="operations-audit-copy"
      onClick={() => {
        void copyValue();
      }}
    >
      {copied ? "Copied" : label}
    </button>
  );
}

export function AuditWorkspace() {
  const [auditEvents, setAuditEvents] =
    useState<OperationsAuditEvent[]>([]);
  const [auditDraft, setAuditDraft] =
    useState<AuditFilterDraft>(EMPTY_AUDIT_FILTERS);
  const [auditAppliedQuery, setAuditAppliedQuery] =
    useState<OperationsAuditEventQuery>({
      sort: "newest",
      page_size: 50,
    });
  const [auditPage, setAuditPage] =
    useState(1);
  const [auditHasMore, setAuditHasMore] =
    useState(false);
  const [auditTimePreset, setAuditTimePreset] =
    useState("custom");
  const [auditLoaded, setAuditLoaded] =
    useState(false);
  const [auditLoading, setAuditLoading] =
    useState(false);
  const [auditError, setAuditError] =
    useState<string | null>(null);

  async function loadAuditEvents(
    query: OperationsAuditEventQuery = auditAppliedQuery,
    page = 1,
  ): Promise<void> {
    if (auditLoading) {
      return;
    }

    setAuditLoading(true);
    setAuditError(null);

    try {
      const result =
        await getOperationsAuditEvents({
          ...query,
          page,
        });

      setAuditEvents(result.items);
      setAuditPage(result.page);
      setAuditHasMore(result.has_more);
      setAuditLoaded(true);
    } catch (caught) {
      setAuditError(
        caught instanceof Error
          ? caught.message
          : "Unable to load audit events.",
      );
    } finally {
      setAuditLoading(false);
    }
  }

  function applyAuditFilters(
    nextDraft: AuditFilterDraft = auditDraft,
  ): void {
    const query = auditQueryFromDraft(nextDraft);
    setAuditAppliedQuery(query);
    void loadAuditEvents(query, 1);
  }

  function resetAuditFilters(): void {
    const nextDraft = { ...EMPTY_AUDIT_FILTERS };
    const query = auditQueryFromDraft(nextDraft);
    setAuditDraft(nextDraft);
    setAuditTimePreset("custom");
    setAuditAppliedQuery(query);
    void loadAuditEvents(query, 1);
  }

  function setAuditPreset(
    preset: "15m" | "1h" | "24h" | "today" | "yesterday" | "custom",
  ): void {
    setAuditTimePreset(preset);

    if (preset === "custom") {
      return;
    }

    const now = new Date();
    let from = new Date(now);
    let to = new Date(now);

    if (preset === "15m") {
      from = new Date(now.getTime() - 15 * 60_000);
    } else if (preset === "1h") {
      from = new Date(now.getTime() - 60 * 60_000);
    } else if (preset === "24h") {
      from = new Date(now.getTime() - 24 * 60 * 60_000);
    } else if (preset === "today") {
      from = new Date(
        now.getFullYear(),
        now.getMonth(),
        now.getDate(),
      );
    } else {
      from = new Date(
        now.getFullYear(),
        now.getMonth(),
        now.getDate() - 1,
      );
      to = new Date(
        now.getFullYear(),
        now.getMonth(),
        now.getDate(),
      );
    }

    const nextDraft = {
      ...auditDraft,
      fromLocal: localDateTimeValue(from),
      toLocal: localDateTimeValue(to),
    };

    setAuditDraft(nextDraft);
    applyAuditFilters(nextDraft);
  }

  function showAuditEventsAround(
    auditEvent: OperationsAuditEvent,
  ): void {
    const center = new Date(auditEvent.created_at);
    const nextDraft = {
      ...auditDraft,
      fromLocal: localDateTimeValue(
        new Date(center.getTime() - 5 * 60_000),
      ),
      toLocal: localDateTimeValue(
        new Date(center.getTime() + 5 * 60_000),
      ),
    };
    const query = auditQueryFromDraft(nextDraft);

    setAuditDraft(nextDraft);
    setAuditTimePreset("custom");
    setAuditAppliedQuery(query);
    void loadAuditEvents(query, 1);
  }

  function exportAuditPage(
    format: "json" | "csv",
  ): void {
    const safeRows = auditEvents.map((auditEvent) => ({
      timestamp: auditEvent.created_at,
      outcome: auditEvent.outcome,
      action: auditEvent.action,
      entity_type: auditEvent.entity_type,
      entity_id: auditEvent.entity_id,
      actor_user_id: auditEvent.actor_user_id,
      actor_email: auditEvent.actor_email,
      environment: auditEvent.environment,
      request_id: auditEvent.request_id,
      error_category: auditEvent.error_category,
      endpoint: auditEvent.endpoint,
      error_code: auditEvent.error_code,
      audit_event_id: auditEvent.id,
    }));

    const content = format === "json"
      ? JSON.stringify(safeRows, null, 2)
      : [
          [
            "timestamp",
            "outcome",
            "action",
            "entity_type",
            "entity_id",
            "actor_user_id",
            "actor_email",
            "environment",
            "request_id",
            "error_category",
            "endpoint",
            "error_code",
            "audit_event_id",
          ].map(csvCell).join(","),
          ...safeRows.map((row) => [
            row.timestamp,
            row.outcome,
            row.action,
            row.entity_type,
            row.entity_id,
            row.actor_user_id,
            row.actor_email,
            row.environment,
            row.request_id,
            row.error_category,
            row.endpoint,
            row.error_code,
            row.audit_event_id,
          ].map(csvCell).join(",")),
        ].join("\n");

    const blob = new Blob([content], {
      type: format === "json"
        ? "application/json"
        : "text/csv",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `dacqua-audit-page-${auditPage}.${format}`;
    link.click();
    URL.revokeObjectURL(url);
  }

  const auditActionOptions = useMemo(
    () => Array.from(
      new Set(auditEvents.map((event) => event.action)),
    ).sort(),
    [auditEvents],
  );

  const auditEntityOptions = useMemo(
    () => Array.from(
      new Set(auditEvents.map((event) => event.entity_type)),
    ).sort(),
    [auditEvents],
  );

  return (
    <div
      id="audit-events"
      className="operations-audit-section"
    >
      <details
        className="operations-audit-disclosure operations-disclosure"
        onToggle={(event) => {
          if (
            event.currentTarget.open
            && !auditLoaded
          ) {
            void loadAuditEvents();
          }
        }}
      >
        <summary>
          <span>
            <strong>Audit log</strong>
            <small>
              Privileged troubleshooting and scheduled review
            </small>
          </span>
        </summary>

        <div className="operations-audit-content">
          <div className="operations-section-heading">
            <p className="eyebrow">
              Audit Events
            </p>
            <h2>Privileged activity history</h2>
            <p>
              Sensitive metadata, IP addresses, and user-agent
              details are intentionally excluded.
            </p>
          </div>

          {auditLoading && !auditLoaded ? (
            <p className="account-muted">
              Loading audit events…
            </p>
          ) : (
            <>
              {auditError !== null ? (
                <p className="account-muted">
                  {auditError}
                </p>
              ) : null}

              <div className="operations-audit-presets" aria-label="Audit time presets">
                {[
                  ["15m", "Last 15 min"],
                  ["1h", "Last hour"],
                  ["24h", "Last 24 hours"],
                  ["today", "Today"],
                  ["yesterday", "Yesterday"],
                  ["custom", "Custom"],
                ].map(([value, label]) => (
                  <button
                    key={value}
                    type="button"
                    className={
                      auditTimePreset === value
                        ? "is-active"
                        : ""
                    }
                    onClick={() => setAuditPreset(
                      value as "15m" | "1h" | "24h" | "today" | "yesterday" | "custom",
                    )}
                  >
                    {label}
                  </button>
                ))}
              </div>

              <p className="operations-governance-context">
                Time filters use {Intl.DateTimeFormat().resolvedOptions().timeZone || "your local timezone"} and are sent to the API as UTC. This screen paginates stored audit records; it does not delete or expire them.
              </p>

              <div className="operations-audit-controls operations-audit-controls-expanded">
                <label className="operations-field operations-customer-search">
                  <span>Search</span>
                  <input
                    {...exactEntryProps}
                    type="search"
                    placeholder="Action code, entity, actor, request ID…"
                    value={auditDraft.search}
                    onChange={(event) => setAuditDraft({
                      ...auditDraft,
                      search: event.target.value,
                    })}
                  />
                </label>

                <label className="operations-field">
                  <span>From</span>
                  <input
                    type="datetime-local"
                    value={auditDraft.fromLocal}
                    onChange={(event) => {
                      setAuditTimePreset("custom");
                      setAuditDraft({
                        ...auditDraft,
                        fromLocal: event.target.value,
                      });
                    }}
                  />
                </label>

                <label className="operations-field">
                  <span>To</span>
                  <input
                    type="datetime-local"
                    value={auditDraft.toLocal}
                    onChange={(event) => {
                      setAuditTimePreset("custom");
                      setAuditDraft({
                        ...auditDraft,
                        toLocal: event.target.value,
                      });
                    }}
                  />
                </label>

                <label className="operations-field">
                  <span>Outcome</span>
                  <select
                    value={auditDraft.outcome}
                    onChange={(event) => setAuditDraft({
                      ...auditDraft,
                      outcome: event.target.value as AuditFilterDraft["outcome"],
                    })}
                  >
                    <option value="all">All outcomes</option>
                    <option value="succeeded">Succeeded</option>
                    <option value="failed">Failed</option>
                  </select>
                </label>

                <label className="operations-field">
                  <span>Action</span>
                  <input
                    {...exactEntryProps}
                    list="audit-action-options"
                    placeholder="Exact action code"
                    value={auditDraft.action}
                    onChange={(event) => setAuditDraft({
                      ...auditDraft,
                      action: event.target.value,
                    })}
                  />
                  <datalist id="audit-action-options">
                    {auditActionOptions.map((action) => (
                      <option key={action} value={action}>
                        {auditActionLabel(action)}
                      </option>
                    ))}
                  </datalist>
                </label>

                <label className="operations-field">
                  <span>Entity type</span>
                  <input
                    {...exactEntryProps}
                    list="audit-entity-options"
                    placeholder="Exact entity type"
                    value={auditDraft.entityType}
                    onChange={(event) => setAuditDraft({
                      ...auditDraft,
                      entityType: event.target.value,
                    })}
                  />
                  <datalist id="audit-entity-options">
                    {auditEntityOptions.map((entityType) => (
                      <option key={entityType} value={entityType}>
                        {auditEntityLabel(entityType)}
                      </option>
                    ))}
                  </datalist>
                </label>

                <label className="operations-field">
                  <span>Entity ID</span>
                  <input
                    {...exactEntryProps}
                    type="search"
                    placeholder="Full or partial ID"
                    value={auditDraft.entityId}
                    onChange={(event) => setAuditDraft({
                      ...auditDraft,
                      entityId: event.target.value,
                    })}
                  />
                </label>

                <label className="operations-field">
                  <span>Actor</span>
                  <input
                    {...exactEntryProps}
                    type="search"
                    placeholder="Email or user ID"
                    value={auditDraft.actor}
                    onChange={(event) => setAuditDraft({
                      ...auditDraft,
                      actor: event.target.value,
                    })}
                  />
                </label>

                <label className="operations-field">
                  <span>Environment</span>
                  <select
                    value={auditDraft.environment}
                    onChange={(event) => setAuditDraft({
                      ...auditDraft,
                      environment: event.target.value,
                    })}
                  >
                    <option value="">All environments</option>
                    <option value="production">Production</option>
                    <option value="development">Development</option>
                    <option value="test">Test</option>
                  </select>
                </label>

                <label className="operations-field">
                  <span>Request ID</span>
                  <input
                    {...exactEntryProps}
                    type="search"
                    placeholder="Full or partial request ID"
                    value={auditDraft.requestId}
                    onChange={(event) => setAuditDraft({
                      ...auditDraft,
                      requestId: event.target.value,
                    })}
                  />
                </label>

                <label className="operations-field">
                  <span>Sort</span>
                  <select
                    value={auditDraft.sort}
                    onChange={(event) => setAuditDraft({
                      ...auditDraft,
                      sort: event.target.value as AuditFilterDraft["sort"],
                    })}
                  >
                    <option value="newest">Newest first</option>
                    <option value="oldest">Oldest first</option>
                  </select>
                </label>
              </div>

              <div className="operations-audit-toolbar">
                <div>
                  <button
                    type="button"
                    className="button button-primary"
                    disabled={auditLoading}
                    onClick={() => applyAuditFilters()}
                  >
                    {auditLoading ? "Loading…" : "Apply filters"}
                  </button>
                  <button
                    type="button"
                    className="button button-secondary"
                    disabled={auditLoading}
                    onClick={resetAuditFilters}
                  >
                    Reset
                  </button>
                </div>

                <div>
                  <button
                    type="button"
                    className="button button-secondary"
                    disabled={auditEvents.length === 0}
                    onClick={() => exportAuditPage("csv")}
                  >
                    Export page CSV
                  </button>
                  <button
                    type="button"
                    className="button button-secondary"
                    disabled={auditEvents.length === 0}
                    onClick={() => exportAuditPage("json")}
                  >
                    Export page JSON
                  </button>
                </div>
              </div>

              <p className="operations-governance-context">
                Page {auditPage} · up to 50 safe audit records. Export contains only the fields visible to this privileged Audit Log API; raw metadata, IP addresses, and user-agent details remain excluded.
              </p>

              {auditEvents.length === 0 ? (
                <p className="account-muted">
                  No audit events match these filters.
                </p>
              ) : (
                <div className="operations-audit-table-wrap">
                  <table className="operations-audit-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Outcome</th>
                        <th>Action</th>
                        <th>Entity</th>
                        <th>Actor</th>
                        <th>Request ID</th>
                        <th>Details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {auditEvents.map((auditEvent) => (
                        <tr key={auditEvent.id}>
                          <td>
                            <span>{new Date(auditEvent.created_at).toLocaleString()}</span>
                            <CopyAuditValueButton
                              value={auditEvent.created_at}
                              label="Copy time"
                            />
                          </td>
                          <td>
                            <span className={`operations-audit-outcome is-${auditEvent.outcome}`}>
                              {auditEvent.outcome === "failed" ? "Failed" : "Succeeded"}
                            </span>
                          </td>
                          <td>
                            <strong>{auditActionLabel(auditEvent.action)}</strong>
                            <code>{auditEvent.action}</code>
                            <CopyAuditValueButton
                              value={auditEvent.action}
                              label="Copy action"
                            />
                          </td>
                          <td>
                            <span>{auditEntityLabel(auditEvent.entity_type)}</span>
                            <code>{auditEvent.entity_id ?? "—"}</code>
                            {auditEvent.entity_id ? (
                              <CopyAuditValueButton
                                value={auditEvent.entity_id}
                                label="Copy ID"
                              />
                            ) : null}
                          </td>
                          <td>
                            <span>
                              {auditEvent.actor_email
                                ?? (auditEvent.actor_user_id
                                  ? "Employee account"
                                  : "System / unauthenticated")}
                            </span>
                            {auditEvent.actor_user_id ? (
                              <code>{auditEvent.actor_user_id}</code>
                            ) : null}
                          </td>
                          <td>
                            <code>{auditEvent.request_id ?? "—"}</code>
                            {auditEvent.request_id ? (
                              <CopyAuditValueButton
                                value={auditEvent.request_id}
                                label="Copy request"
                              />
                            ) : null}
                          </td>
                          <td>
                            <details className="operations-audit-row-details">
                              <summary>View</summary>
                              <div>
                                <p><strong>Environment:</strong> {auditEvent.environment}</p>
                                <p><strong>Audit event:</strong> <code>{auditEvent.id}</code></p>
                                {auditEvent.endpoint ? (
                                  <p><strong>Endpoint:</strong> <code>{auditEvent.endpoint}</code></p>
                                ) : null}
                                {auditEvent.error_category ? (
                                  <p><strong>Error category:</strong> {auditEvent.error_category}</p>
                                ) : null}
                                {auditEvent.error_code ? (
                                  <p><strong>Error code:</strong> <code>{auditEvent.error_code}</code></p>
                                ) : null}
                                <div className="operations-audit-detail-actions">
                                  <CopyAuditValueButton
                                    value={auditEvent.id}
                                    label="Copy audit ID"
                                  />
                                  <button
                                    type="button"
                                    className="operations-audit-copy"
                                    onClick={() => showAuditEventsAround(auditEvent)}
                                  >
                                    Events ±5 min
                                  </button>
                                </div>
                              </div>
                            </details>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <div className="operations-audit-pagination">
                <button
                  type="button"
                  className="button button-secondary"
                  disabled={auditLoading || auditPage <= 1}
                  onClick={() => {
                    void loadAuditEvents(
                      auditAppliedQuery,
                      auditPage - 1,
                    );
                  }}
                >
                  Previous
                </button>
                <span>Page {auditPage}</span>
                <button
                  type="button"
                  className="button button-secondary"
                  disabled={auditLoading || !auditHasMore}
                  onClick={() => {
                    void loadAuditEvents(
                      auditAppliedQuery,
                      auditPage + 1,
                    );
                  }}
                >
                  Next
                </button>
              </div>
            </>
          )}
        </div>
      </details>
    </div>
  );
}
