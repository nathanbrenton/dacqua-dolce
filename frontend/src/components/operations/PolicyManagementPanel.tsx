import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  approvePolicyDocument,
  createPolicyDraft,
  getOperationsPolicies,
  type PolicyDocument,
  type PolicyKind,
} from "../../api/policies";

const POLICY_OPTIONS: Array<{
  kind: PolicyKind;
  label: string;
}> = [
  { kind: "privacy", label: "Privacy" },
  { kind: "terms", label: "Terms & Policies" },
  { kind: "shipping", label: "Shipping Policy" },
  { kind: "cancellation", label: "Cancellation Policy" },
  { kind: "refund", label: "Refund Policy" },
  { kind: "warranty", label: "Warranty" },
  { kind: "installation", label: "Installation Terms" },
];

type PolicyManagementPanelProps = {
  roles: string[];
};

export function PolicyManagementPanel({
  roles,
}: PolicyManagementPanelProps) {
  const writable = roles.some(
    (role) => role === "administrator" || role === "developer",
  );
  const [policies, setPolicies] =
    useState<PolicyDocument[]>([]);
  const [kind, setKind] =
    useState<PolicyKind>("terms");
  const [version, setVersion] =
    useState("");
  const [title, setTitle] =
    useState("");
  const [body, setBody] =
    useState("");
  const [busy, setBusy] =
    useState(false);
  const [message, setMessage] =
    useState<string | null>(null);
  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    void getOperationsPolicies()
      .then((rows) => {
        if (!cancelled) {
          setPolicies(rows);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(
            caught instanceof Error
              ? caught.message
              : "Policy versions could not be loaded.",
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const grouped = useMemo(() => {
    const result = new Map<PolicyKind, PolicyDocument[]>();

    for (const option of POLICY_OPTIONS) {
      result.set(option.kind, []);
    }

    for (const policy of policies) {
      result.get(policy.kind)?.push(policy);
    }

    return result;
  }, [policies]);

  async function createDraft(): Promise<void> {
    setBusy(true);
    setError(null);
    setMessage(null);

    try {
      const created = await createPolicyDraft({
        kind,
        version,
        title,
        body,
      });
      setPolicies((current) => [created, ...current]);
      setVersion("");
      setTitle("");
      setBody("");
      setMessage(
        `${created.title} version ${created.version} saved as draft.`,
      );
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Policy draft could not be created.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function approve(policy: PolicyDocument): Promise<void> {
    const confirmed = window.confirm(
      `Approve ${policy.title} version ${policy.version}? `
      + "The approved text may be published and attached to newly presented quotes.",
    );
    if (!confirmed) {
      return;
    }

    setBusy(true);
    setError(null);
    setMessage(null);

    try {
      const updated = await approvePolicyDocument(policy.id);
      const refreshed = await getOperationsPolicies();
      setPolicies(refreshed);
      setMessage(
        `${updated.title} version ${updated.version} is approved.`,
      );
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Policy version could not be approved.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="operations-section operations-policy-section">
      <div className="operations-section-heading">
        <div>
          <p className="eyebrow">Launch policies</p>
          <h2>Approved customer terms and policy versions.</h2>
          <p>
            Draft text stays private. Only an explicitly approved version is
            published or snapshotted onto a newly presented formal quote.
          </p>
        </div>
      </div>

      {error !== null ? (
        <p className="operations-alert operations-error" role="alert">
          {error}
        </p>
      ) : null}

      {message !== null ? (
        <p className="operations-alert" role="status">
          {message}
        </p>
      ) : null}

      <div className="operations-policy-grid">
        {POLICY_OPTIONS.map((option) => {
          const rows = grouped.get(option.kind) ?? [];
          const approved = rows.find((row) => row.status === "approved") ?? null;

          return (
            <article key={option.kind} className="operations-policy-card">
              <header>
                <strong>{option.label}</strong>
                <span>
                  {approved === null
                    ? "No approved version"
                    : `Approved · ${approved.version}`}
                </span>
              </header>

              {rows.length === 0 ? (
                <p>No versions recorded.</p>
              ) : (
                <div className="operations-policy-history">
                  {rows.map((policy) => (
                    <div key={policy.id}>
                      <div>
                        <strong>{policy.version}</strong>
                        <span>{policy.status}</span>
                      </div>
                      <span>{policy.title}</span>
                      {policy.status === "draft" && writable ? (
                        <button
                          type="button"
                          className="operations-action secondary"
                          disabled={busy}
                          onClick={() => {
                            void approve(policy);
                          }}
                        >
                          Approve version
                        </button>
                      ) : null}
                    </div>
                  ))}
                </div>
              )}
            </article>
          );
        })}
      </div>

      {writable ? (
        <div className="operations-policy-editor">
          <h3>Create a new draft version</h3>

          <label className="operations-field">
            <span>Policy</span>
            <select
              value={kind}
              onChange={(event) => {
                setKind(event.target.value as PolicyKind);
              }}
            >
              {POLICY_OPTIONS.map((option) => (
                <option key={option.kind} value={option.kind}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="operations-field">
            <span>Version</span>
            <input
              value={version}
              onChange={(event) => setVersion(event.target.value)}
              placeholder="Example: 2026-10-01"
            />
          </label>

          <label className="operations-field">
            <span>Title</span>
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Approved customer-facing title"
            />
          </label>

          <label className="operations-field">
            <span>Policy text</span>
            <textarea
              rows={12}
              value={body}
              onChange={(event) => setBody(event.target.value)}
              placeholder="Paste externally reviewed policy text here."
            />
          </label>

          <button
            type="button"
            className="operations-action"
            disabled={
              busy
              || version.trim() === ""
              || title.trim() === ""
              || body.trim() === ""
            }
            onClick={() => {
              void createDraft();
            }}
          >
            Save draft version
          </button>
        </div>
      ) : (
        <p className="operations-request-empty">
          Employees can review policy status. Administrator or developer
          authorization is required to create or approve versions.
        </p>
      )}
    </section>
  );
}
