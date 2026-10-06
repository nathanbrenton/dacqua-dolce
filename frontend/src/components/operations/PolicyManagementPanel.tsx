import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  applyPolicyImport,
  approvePolicyDocument,
  createPolicyDraft,
  exportPolicyBundle,
  getOperationsPolicies,
  previewPolicyImport,
  type PolicyDocument,
  type PolicyExportBundle,
  type PolicyExportScope,
  type PolicyImportMode,
  type PolicyImportReport,
  type PolicyKind,
  type RefundPolicyTerms,
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

function refundTermsSummary(terms: RefundPolicyTerms): string {
  const eligibility = terms.eligibility_mode === "case_by_case"
    ? "case-by-case eligibility"
    : terms.eligibility_mode === "fixed_window"
      ? `${terms.return_window_days ?? "?"}-day window`
      : `${terms.return_window_days ?? "?"}-day window + case-by-case exception`;

  const restocking = terms.restocking_mode === "case_by_case"
    ? "case-by-case restocking"
    : `${((terms.restocking_fee_basis_points ?? 0) / 100).toFixed(2)}% restocking`;

  return `${eligibility}; ${restocking}`;
}

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
  const [configureRefundTerms, setConfigureRefundTerms] =
    useState(false);
  const [refundEligibilityMode, setRefundEligibilityMode] =
    useState<RefundPolicyTerms["eligibility_mode"] | "">("");
  const [returnWindowDays, setReturnWindowDays] =
    useState("");
  const [restockingMode, setRestockingMode] =
    useState<RefundPolicyTerms["restocking_mode"] | "">("");
  const [restockingPercent, setRestockingPercent] =
    useState("");
  const [busy, setBusy] =
    useState(false);
  const [message, setMessage] =
    useState<string | null>(null);
  const [error, setError] =
    useState<string | null>(null);
  const [draftSaveFeedback, setDraftSaveFeedback] =
    useState<{
      kind: "success" | "error";
      text: string;
    } | null>(null);
  const draftSaveInFlight = useRef(false);
  const [exportScope, setExportScope] =
    useState<PolicyExportScope>("all");
  const [importBundle, setImportBundle] =
    useState<PolicyExportBundle | null>(null);
  const [importMode, setImportMode] =
    useState<PolicyImportMode>("draft_only");
  const [importReport, setImportReport] =
    useState<PolicyImportReport | null>(null);

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

  const refundTerms = useMemo<RefundPolicyTerms | null>(() => {
    if (kind !== "refund" || !configureRefundTerms) {
      return null;
    }

    if (refundEligibilityMode === "" || restockingMode === "") {
      return null;
    }

    const requiresWindow = refundEligibilityMode !== "case_by_case";
    const parsedWindow = requiresWindow
      ? Number.parseInt(returnWindowDays, 10)
      : null;
    if (
      requiresWindow
      && (
        parsedWindow === null
        || Number.isNaN(parsedWindow)
        || parsedWindow < 1
        || parsedWindow > 365
      )
    ) {
      return null;
    }

    const requiresPercentage = restockingMode === "fixed_percentage";
    const parsedPercent = requiresPercentage
      ? Number.parseFloat(restockingPercent)
      : null;
    if (
      requiresPercentage
      && (
        parsedPercent === null
        || Number.isNaN(parsedPercent)
        || parsedPercent <= 0
        || parsedPercent > 100
      )
    ) {
      return null;
    }

    return {
      eligibility_mode: refundEligibilityMode,
      return_window_days: requiresWindow ? parsedWindow : null,
      restocking_mode: restockingMode,
      restocking_fee_basis_points: requiresPercentage
        ? Math.round((parsedPercent ?? 0) * 100)
        : null,
      merchandise_condition: "new_uninstalled",
      customer_pays_return_shipping_by_default: true,
      outbound_shipping_refund_rule:
        "nonrefundable_with_error_defect_or_discretion_exception",
      acknowledgement_required: true,
    };
  }, [
    configureRefundTerms,
    kind,
    refundEligibilityMode,
    restockingMode,
    restockingPercent,
    returnWindowDays,
  ]);

  const refundTermsInvalid =
    kind === "refund"
    && configureRefundTerms
    && refundTerms === null;

  function beginSuccessorDraft(policy: PolicyDocument): void {
    setKind(policy.kind);
    setVersion("");
    setTitle(policy.title);
    setBody(policy.body);

    if (policy.kind === "refund" && policy.refund_terms !== null) {
      setConfigureRefundTerms(true);
      setRefundEligibilityMode(policy.refund_terms.eligibility_mode);
      setReturnWindowDays(
        policy.refund_terms.return_window_days === null
          ? ""
          : String(policy.refund_terms.return_window_days),
      );
      setRestockingMode(policy.refund_terms.restocking_mode);
      setRestockingPercent(
        policy.refund_terms.restocking_fee_basis_points === null
          ? ""
          : String(
              policy.refund_terms.restocking_fee_basis_points / 100,
            ),
      );
    } else {
      setConfigureRefundTerms(false);
      setRefundEligibilityMode("");
      setReturnWindowDays("");
      setRestockingMode("");
      setRestockingPercent("");
    }

    setMessage(
      `Started a new draft from ${policy.title} version ${policy.version}.`,
    );
    setError(null);
    setDraftSaveFeedback(null);
  }

  async function createDraft(): Promise<void> {
    if (draftSaveInFlight.current) {
      return;
    }

    draftSaveInFlight.current = true;
    setBusy(true);
    setError(null);
    setMessage(null);
    setDraftSaveFeedback(null);

    try {
      const created = await createPolicyDraft({
        kind,
        version,
        title,
        body,
        refund_terms: refundTerms,
      });
      setPolicies((current) => [created, ...current]);
      setVersion("");
      setTitle("");
      setBody("");
      setConfigureRefundTerms(false);
      setRefundEligibilityMode("");
      setReturnWindowDays("");
      setRestockingMode("");
      setRestockingPercent("");
      const savedMessage =
        `${created.title} version ${created.version} saved as draft.`;
      setMessage(savedMessage);
      setDraftSaveFeedback({
        kind: "success",
        text: savedMessage,
      });
    } catch (caught) {
      const saveError =
        caught instanceof Error
          ? caught.message
          : "Policy draft could not be created.";
      setError(saveError);
      setDraftSaveFeedback({
        kind: "error",
        text: saveError,
      });
    } finally {
      draftSaveInFlight.current = false;
      setBusy(false);
    }
  }

  async function downloadExport(): Promise<void> {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const bundle = await exportPolicyBundle(exportScope);
      const blob = new Blob(
        [JSON.stringify(bundle, null, 2) + "\n"],
        { type: "application/json" },
      );
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const day = new Date().toISOString().slice(0, 10);
      anchor.href = url;
      anchor.download = `dacqua-dolce-policies-${day}-${exportScope}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      setMessage(`Exported ${bundle.policies.length} policy versions.`);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Policy export could not be created.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function loadImportFile(file: File | null): Promise<void> {
    setImportBundle(null);
    setImportReport(null);
    setError(null);
    setMessage(null);
    if (file === null) {
      return;
    }
    try {
      const parsed = JSON.parse(await file.text()) as PolicyExportBundle;
      setImportBundle(parsed);
      setMessage(`Loaded policy bundle from ${file.name}. Preview before applying.`);
    } catch {
      setError("That file is not valid JSON.");
    }
  }

  async function previewImport(): Promise<void> {
    if (importBundle === null) {
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const report = await previewPolicyImport(importBundle, importMode);
      setImportReport(report);
      setMessage("Import preview completed. No policy data was changed.");
    } catch (caught) {
      setImportReport(null);
      setError(
        caught instanceof Error
          ? caught.message
          : "Policy import preview failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function applyImport(): Promise<void> {
    if (importBundle === null || importReport === null || importReport.conflicts > 0) {
      return;
    }
    const confirmed = window.confirm(
      importMode === "preserve_lifecycle"
        ? "Apply this lifecycle-preserving policy import? This mode is intended only for non-production synchronization."
        : "Import the missing policy versions as drafts? Existing versions will not be overwritten or deleted.",
    );
    if (!confirmed) {
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const report = await applyPolicyImport(importBundle, importMode);
      setImportReport(report);
      setPolicies(await getOperationsPolicies());
      setMessage(
        `Policy import applied: ${report.additions} added, ${report.skips} skipped, ${report.lifecycle_updates} lifecycle updates.`,
      );
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Policy import could not be applied.",
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
    <section className="operations-policy-section">
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


      <div className="operations-policy-editor">
        <h3>Policy portability</h3>
        <p className="operations-request-empty">
          Export policy versions without customer data or credentials. Imports are
          previewed first, never delete destination-only versions, and never overwrite
          conflicting policy content.
        </p>

        <div className="operations-field-row">
          <label className="operations-field">
            <span>Export scope</span>
            <select
              value={exportScope}
              onChange={(event) => {
                setExportScope(event.target.value as PolicyExportScope);
              }}
            >
              <option value="all">All policy versions</option>
              <option value="approved_effective">Approved/effective only</option>
            </select>
          </label>
          <button
            type="button"
            className="operations-action secondary"
            disabled={busy}
            onClick={() => {
              void downloadExport();
            }}
          >
            Export policies
          </button>
        </div>

        {writable ? (
          <>
            <label className="operations-field">
              <span>Import policy bundle</span>
              <input
                type="file"
                accept="application/json,.json"
                disabled={busy}
                onChange={(event) => {
                  void loadImportFile(event.target.files?.[0] ?? null);
                }}
              />
            </label>

            <label className="operations-field">
              <span>Import mode</span>
              <select
                value={importMode}
                disabled={busy}
                onChange={(event) => {
                  setImportMode(event.target.value as PolicyImportMode);
                  setImportReport(null);
                }}
              >
                <option value="draft_only">Safe import — add missing versions as drafts</option>
                <option value="preserve_lifecycle">Non-production mirror — preserve lifecycle</option>
              </select>
            </label>

            {importMode === "preserve_lifecycle" ? (
              <p className="operations-request-empty">
                Lifecycle preservation is for Local/Dev/Test synchronization only and
                requires DACQUA_POLICY_IMPORT_ALLOW_LIFECYCLE_PRESERVATION=true on that
                environment. Production should normally use safe draft-only import.
              </p>
            ) : null}

            <button
              type="button"
              className="operations-action secondary"
              disabled={busy || importBundle === null}
              onClick={() => {
                void previewImport();
              }}
            >
              Preview import
            </button>

            {importReport !== null ? (
              <div className="operations-policy-history" role="status">
                <div>
                  <strong>Import preview</strong>
                  <span>
                    {importReport.additions} add · {importReport.skips} skip · {importReport.conflicts} conflict · {importReport.lifecycle_updates} lifecycle update · {importReport.destination_retirements} destination retirement
                  </span>
                </div>
                {importReport.actions.map((action) => (
                  <div key={`${action.kind}-${action.version}-${action.action}`}>
                    <strong>{action.kind} · {action.version}</strong>
                    <span>{action.action.replaceAll("_", " ")}</span>
                    <span>{action.detail}</span>
                  </div>
                ))}
              </div>
            ) : null}

            <button
              type="button"
              className="operations-action"
              disabled={
                busy
                || importBundle === null
                || importReport === null
                || importReport.conflicts > 0
              }
              onClick={() => {
                void applyImport();
              }}
            >
              Apply previewed import
            </button>
          </>
        ) : (
          <p className="operations-request-empty">
            Operations staff can export policy bundles. Administrator or developer
            authorization is required to preview or apply imports.
          </p>
        )}
      </div>

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
                      {policy.kind === "refund" && policy.refund_terms !== null ? (
                        <span>
                          Structured terms: {refundTermsSummary(policy.refund_terms)}
                        </span>
                      ) : null}
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
                      {policy.status === "approved" && writable ? (
                        <button
                          type="button"
                          className="operations-action secondary"
                          disabled={busy}
                          onClick={() => {
                            beginSuccessorDraft(policy);
                          }}
                        >
                          Start successor draft
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

          {kind === "refund" ? (
            <div className="operations-policy-editor">
              <label className="operations-field">
                <span>Structured return settings</span>
                <span>
                  <input
                    type="checkbox"
                    checked={configureRefundTerms}
                    onChange={(event) => {
                      setConfigureRefundTerms(event.target.checked);
                    }}
                  />
                  {" "}Attach machine-readable return/restocking terms to this version.
                </span>
              </label>

              {configureRefundTerms ? (
                <>
                  <label className="operations-field">
                    <span>Return eligibility</span>
                    <select
                      value={refundEligibilityMode}
                      onChange={(event) => {
                        setRefundEligibilityMode(
                          event.target.value as RefundPolicyTerms["eligibility_mode"] | "",
                        );
                      }}
                    >
                      <option value="">Select a rule</option>
                      <option value="fixed_window">Fixed return window</option>
                      <option value="case_by_case">Case-by-case approval</option>
                      <option value="fixed_window_with_exception">
                        Fixed window with case-by-case exception
                      </option>
                    </select>
                  </label>

                  {refundEligibilityMode !== ""
                    && refundEligibilityMode !== "case_by_case" ? (
                      <label className="operations-field">
                        <span>Return window (days)</span>
                        <input
                          type="number"
                          min="1"
                          max="365"
                          value={returnWindowDays}
                          onChange={(event) => {
                            setReturnWindowDays(event.target.value);
                          }}
                          placeholder="Example: 60"
                        />
                      </label>
                    ) : null}

                  <label className="operations-field">
                    <span>Restocking fee</span>
                    <select
                      value={restockingMode}
                      onChange={(event) => {
                        setRestockingMode(
                          event.target.value as RefundPolicyTerms["restocking_mode"] | "",
                        );
                      }}
                    >
                      <option value="">Select a rule</option>
                      <option value="fixed_percentage">Fixed percentage</option>
                      <option value="case_by_case">Case-by-case decision</option>
                    </select>
                  </label>

                  {restockingMode === "fixed_percentage" ? (
                    <label className="operations-field">
                      <span>Restocking percentage</span>
                      <input
                        type="number"
                        min="0.01"
                        max="100"
                        step="0.01"
                        value={restockingPercent}
                        onChange={(event) => {
                          setRestockingPercent(event.target.value);
                        }}
                        placeholder="Example: 25"
                      />
                    </label>
                  ) : null}

                  <p className="operations-request-empty">
                    Structured terms are versioned with this Refund Policy.
                    New/uninstalled merchandise, customer-paid return shipping,
                    outbound-shipping exceptions, and acknowledgement requirements
                    follow the recorded launch direction. Legal policy text remains
                    authoritative and still requires approval before publication.
                  </p>
                </>
              ) : (
                <p className="operations-request-empty">
                  Refund Policy approval requires structured return/restocking
                  terms. Use the approved policy as the starting point when changing
                  terms so a new version can take effect prospectively.
                </p>
              )}
            </div>
          ) : null}

          <button
            type="button"
            className="operations-action"
            disabled={
              busy
              || version.trim() === ""
              || title.trim() === ""
              || body.trim() === ""
              || refundTermsInvalid
            }
            aria-busy={draftSaveInFlight.current}
            onClick={() => {
              void createDraft();
            }}
          >
            {draftSaveInFlight.current ? "Saving draft…" : "Save draft version"}
          </button>

          {draftSaveFeedback !== null ? (
            <p
              className={
                draftSaveFeedback.kind === "error"
                  ? "operations-alert operations-error"
                  : "operations-alert"
              }
              role={draftSaveFeedback.kind === "error" ? "alert" : "status"}
            >
              {draftSaveFeedback.text}
            </p>
          ) : null}
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
