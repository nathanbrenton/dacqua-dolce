import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getLaunchDependencyEvidence,
  updateLaunchDependencyEvidence,
  type LaunchDependencyTrackingStatus,
  type OperationsLaunchDependencyEvidence,
} from "../../api/operations";

type LaunchDependencyEvidencePanelProps = {
  roles: string[];
};

type EvidenceDraft = {
  trackingStatus: LaunchDependencyTrackingStatus;
  sourceReference: string;
  receivedLocal: string;
  internalNotes: string;
};

const WRITE_ROLES = new Set([
  "administrator",
  "developer",
]);

const STATUS_OPTIONS: Array<{
  value: LaunchDependencyTrackingStatus;
  label: string;
}> = [
  { value: "action_required", label: "Action required" },
  { value: "in_progress", label: "In progress" },
  { value: "evidence_received", label: "Evidence received" },
  { value: "verified", label: "Evidence verified" },
  { value: "blocked", label: "Blocked" },
];

function localDateTimeValue(value: string | null): string {
  if (!value) {
    return "";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const local = new Date(
    date.getTime() - date.getTimezoneOffset() * 60_000,
  );
  return local.toISOString().slice(0, 16);
}

function draftFor(
  evidence: OperationsLaunchDependencyEvidence,
): EvidenceDraft {
  return {
    trackingStatus: evidence.tracking_status,
    sourceReference: evidence.source_reference ?? "",
    receivedLocal: localDateTimeValue(evidence.evidence_received_at),
    internalNotes: evidence.internal_notes ?? "",
  };
}

function statusLabel(status: LaunchDependencyTrackingStatus): string {
  return STATUS_OPTIONS.find((option) => option.value === status)?.label
    ?? status.replaceAll("_", " ");
}

export function LaunchDependencyEvidencePanel({
  roles,
}: LaunchDependencyEvidencePanelProps) {
  const canWrite = useMemo(
    () => roles.some((role) => WRITE_ROLES.has(role)),
    [roles],
  );
  const [items, setItems] =
    useState<OperationsLaunchDependencyEvidence[]>([]);
  const [drafts, setDrafts] =
    useState<Record<string, EvidenceDraft>>({});
  const [saving, setSaving] =
    useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    void getLaunchDependencyEvidence()
      .then((result) => {
        if (cancelled) {
          return;
        }
        setItems(result);
        setDrafts(
          Object.fromEntries(
            result.map((item) => [
              item.dependency_key,
              draftFor(item),
            ]),
          ),
        );
        setError(null);
      })
      .catch((reason: unknown) => {
        if (cancelled) {
          return;
        }
        setError(
          reason instanceof Error
            ? reason.message
            : "Unable to load launch dependency evidence.",
        );
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  async function saveEvidence(
    evidence: OperationsLaunchDependencyEvidence,
  ): Promise<void> {
    const draft = drafts[evidence.dependency_key];
    if (!draft || saving[evidence.dependency_key]) {
      return;
    }

    setSaving((current) => ({
      ...current,
      [evidence.dependency_key]: true,
    }));
    setError(null);

    try {
      const updated = await updateLaunchDependencyEvidence(
        evidence.dependency_key,
        {
          tracking_status: draft.trackingStatus,
          source_reference: draft.sourceReference.trim() || null,
          evidence_received_at: draft.receivedLocal
            ? new Date(draft.receivedLocal).toISOString()
            : null,
          internal_notes: draft.internalNotes.trim() || null,
        },
      );

      setItems((current) => current.map((item) => (
        item.dependency_key === updated.dependency_key
          ? updated
          : item
      )));
      setDrafts((current) => ({
        ...current,
        [updated.dependency_key]: draftFor(updated),
      }));
    } catch (reason: unknown) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Unable to save launch dependency evidence.",
      );
    } finally {
      setSaving((current) => ({
        ...current,
        [evidence.dependency_key]: false,
      }));
    }
  }

  if (loading) {
    return (
      <div className="operations-insight-lists">
        <div>
          <strong>External commissioning evidence</strong>
          <p>Loading internal evidence tracking…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="operations-insight-lists">
      <div>
        <strong>External commissioning evidence</strong>
        <p>
          Internal tracking only. These statuses do not open the Commerce
          Launch Gate and never replace tax, payment, policy, or other
          service-level checkout guards.
        </p>
        <small>
          Record references and meeting/document provenance only. Do not store
          passwords, API keys, merchant credentials, tax account numbers, or
          other secrets here.
        </small>
      </div>

      {error ? (
        <div role="alert">
          <strong>Evidence tracking error</strong>
          <p>{error}</p>
        </div>
      ) : null}

      {items.map((evidence) => {
        const draft = drafts[evidence.dependency_key] ?? draftFor(evidence);
        const isSaving = saving[evidence.dependency_key] === true;

        return (
          <div key={evidence.dependency_key}>
            <strong>{evidence.label}</strong>

            {canWrite ? (
              <>
                <label className="operations-field compact">
                  <span>Status</span>
                  <select
                    value={draft.trackingStatus}
                    onChange={(event) => {
                      setDrafts((current) => ({
                        ...current,
                        [evidence.dependency_key]: {
                          ...draft,
                          trackingStatus:
                            event.target.value as LaunchDependencyTrackingStatus,
                        },
                      }));
                    }}
                  >
                    {STATUS_OPTIONS.map((option) => (
                      <option
                        key={option.value}
                        value={option.value}
                      >
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="operations-field compact">
                  <span>Source / reference</span>
                  <input
                    type="text"
                    value={draft.sourceReference}
                    maxLength={4000}
                    placeholder="Meeting notes, document name, ticket, or non-secret reference"
                    onChange={(event) => {
                      setDrafts((current) => ({
                        ...current,
                        [evidence.dependency_key]: {
                          ...draft,
                          sourceReference: event.target.value,
                        },
                      }));
                    }}
                  />
                </label>

                <label className="operations-field compact">
                  <span>Evidence received</span>
                  <input
                    type="datetime-local"
                    value={draft.receivedLocal}
                    onChange={(event) => {
                      setDrafts((current) => ({
                        ...current,
                        [evidence.dependency_key]: {
                          ...draft,
                          receivedLocal: event.target.value,
                        },
                      }));
                    }}
                  />
                </label>

                <label className="operations-field compact">
                  <span>Internal notes</span>
                  <textarea
                    value={draft.internalNotes}
                    maxLength={8000}
                    rows={3}
                    placeholder="Non-secret internal commissioning notes"
                    onChange={(event) => {
                      setDrafts((current) => ({
                        ...current,
                        [evidence.dependency_key]: {
                          ...draft,
                          internalNotes: event.target.value,
                        },
                      }));
                    }}
                  />
                </label>

                <button
                  type="button"
                  disabled={isSaving}
                  onClick={() => {
                    void saveEvidence(evidence);
                  }}
                >
                  {isSaving ? "Saving…" : "Save evidence"}
                </button>
              </>
            ) : (
              <>
                <p>{statusLabel(evidence.tracking_status)}</p>
                <small>
                  {evidence.source_reference ?? "No source/reference recorded."}
                  {evidence.evidence_received_at
                    ? ` · Received ${new Date(
                      evidence.evidence_received_at,
                    ).toLocaleString()}`
                    : ""}
                </small>
                {evidence.internal_notes ? (
                  <p>{evidence.internal_notes}</p>
                ) : null}
              </>
            )}

            {evidence.updated_at ? (
              <small>
                Last updated {new Date(evidence.updated_at).toLocaleString()}.
              </small>
            ) : (
              <small>No evidence record has been saved yet.</small>
            )}
          </div>
        );
      })}
    </div>
  );
}
