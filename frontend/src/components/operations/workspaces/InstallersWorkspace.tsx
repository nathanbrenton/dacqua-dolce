/**
 * Installers workspace: internal research registry of installer candidates.
 * Not customer-facing.
 *
 * Data:    src/api/operations.ts
 *            getOperationsInstallerCandidates() -> GET /api/operations/installer-candidates
 *            createInstallerCandidate()         -> POST /api/operations/installer-candidates
 *            updateInstallerCandidate()         -> PUT /api/operations/installer-candidates/{id}
 *          (backend/app/api/operations.py)
 * Tests:   backend/tests/test_installer_candidates.py
 * Loads its own list when Operations opens; editing needs a privileged role.
 */
import { useEffect, useMemo, useState } from "react";

import {
  createInstallerCandidate,
  getOperationsInstallerCandidates,
  updateInstallerCandidate,
  type InstallerCandidateStatus,
  type OperationsInstallerCandidate,
} from "../../../api/operations";
import type { OperationsNoticeProps } from "../operationsShared";

const INSTALLER_CANDIDATE_STATUSES: InstallerCandidateStatus[] = [
  "researching",
  "contacted",
  "review_pending",
  "inactive",
];

const INSTALLER_CANDIDATE_STATUS_LABELS: Record<
  InstallerCandidateStatus,
  string
> = {
  researching: "Researching",
  contacted: "Contacted",
  review_pending: "Review pending",
  inactive: "Inactive",
};

type InstallerCandidateDraft = {
  businessName: string;
  contactName: string;
  email: string;
  phone: string;
  website: string;
  serviceAreaNotes: string;
  sourceReference: string;
  status: InstallerCandidateStatus;
  internalNotes: string;
};

const EMPTY_INSTALLER_CANDIDATE_DRAFT: InstallerCandidateDraft = {
  businessName: "",
  contactName: "",
  email: "",
  phone: "",
  website: "",
  serviceAreaNotes: "",
  sourceReference: "",
  status: "researching",
  internalNotes: "",
};

function installerCandidateDraft(
  candidate: OperationsInstallerCandidate,
): InstallerCandidateDraft {
  return {
    businessName: candidate.business_name,
    contactName: candidate.contact_name ?? "",
    email: candidate.email ?? "",
    phone: candidate.phone ?? "",
    website: candidate.website ?? "",
    serviceAreaNotes: candidate.service_area_notes ?? "",
    sourceReference: candidate.source_reference ?? "",
    status: candidate.status,
    internalNotes: candidate.internal_notes ?? "",
  };
}

type InstallersWorkspaceProps = OperationsNoticeProps & {
  /** Administrators and developers can add and edit candidates. */
  privileged: boolean;
};

export function InstallersWorkspace({
  privileged,
  onMessage: setMessage,
  onError: setError,
}: InstallersWorkspaceProps) {
  const [installerCandidates, setInstallerCandidates] =
    useState<OperationsInstallerCandidate[]>([]);
  const [installerCandidateSearch, setInstallerCandidateSearch] =
    useState("");
  const [installerCandidateCreateDraft, setInstallerCandidateCreateDraft] =
    useState<InstallerCandidateDraft>(EMPTY_INSTALLER_CANDIDATE_DRAFT);
  const [installerCandidateDrafts, setInstallerCandidateDrafts] =
    useState<Record<string, InstallerCandidateDraft>>({});
  const [installerCandidateSaving, setInstallerCandidateSaving] =
    useState<Record<string, boolean>>({});
  const [installerCandidateCreating, setInstallerCandidateCreating] =
    useState(false);

  useEffect(() => {
    let cancelled = false;

    void getOperationsInstallerCandidates()
      .then((result) => {
        if (cancelled) {
          return;
        }
        setInstallerCandidates(result);
        setInstallerCandidateDrafts(
          Object.fromEntries(
            result.map((candidate) => [
              candidate.id,
              installerCandidateDraft(candidate),
            ]),
          ),
        );
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(
            caught instanceof Error
              ? caught.message
              : "Installer candidates could not be loaded.",
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, [setError]);

  const filteredInstallerCandidates = useMemo(() => {
    const query = installerCandidateSearch.trim().toLowerCase();

    if (query.length === 0) {
      return installerCandidates;
    }

    return installerCandidates.filter((candidate) => {
      const searchable = [
        candidate.business_name,
        candidate.contact_name ?? "",
        candidate.email ?? "",
        candidate.phone ?? "",
        candidate.website ?? "",
        candidate.service_area_notes ?? "",
        candidate.source_reference ?? "",
        candidate.status,
        candidate.internal_notes ?? "",
      ].join(" ").toLowerCase();

      return searchable.includes(query);
    });
  }, [installerCandidates, installerCandidateSearch]);

  function installerCandidatePayload(draft: InstallerCandidateDraft) {
    return {
      business_name: draft.businessName.trim(),
      contact_name: draft.contactName.trim() || null,
      email: draft.email.trim() || null,
      phone: draft.phone.trim() || null,
      website: draft.website.trim() || null,
      service_area_notes: draft.serviceAreaNotes.trim() || null,
      source_reference: draft.sourceReference.trim() || null,
      status: draft.status,
      internal_notes: draft.internalNotes.trim() || null,
    };
  }

  async function addInstallerCandidate(): Promise<void> {
    if (!installerCandidateCreateDraft.businessName.trim()) {
      setError("Enter a business name before adding an installer candidate.");
      return;
    }

    setInstallerCandidateCreating(true);
    setError(null);
    try {
      const created = await createInstallerCandidate(
        installerCandidatePayload(installerCandidateCreateDraft),
      );
      setInstallerCandidates((current) => [created, ...current]);
      setInstallerCandidateDrafts((current) => ({
        ...current,
        [created.id]: installerCandidateDraft(created),
      }));
      setInstallerCandidateCreateDraft(EMPTY_INSTALLER_CANDIDATE_DRAFT);
      setMessage("Installer candidate added to the internal research registry.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to add installer candidate.");
    } finally {
      setInstallerCandidateCreating(false);
    }
  }

  async function saveInstallerCandidate(
    candidate: OperationsInstallerCandidate,
  ): Promise<void> {
    const draft = installerCandidateDrafts[candidate.id];
    if (!draft?.businessName.trim()) {
      setError("Business name cannot be blank.");
      return;
    }

    setInstallerCandidateSaving((current) => ({
      ...current,
      [candidate.id]: true,
    }));
    setError(null);
    try {
      const updated = await updateInstallerCandidate(
        candidate.id,
        installerCandidatePayload(draft),
      );
      setInstallerCandidates((current) => current.map((item) => (
        item.id === updated.id ? updated : item
      )));
      setInstallerCandidateDrafts((current) => ({
        ...current,
        [updated.id]: installerCandidateDraft(updated),
      }));
      setMessage("Installer candidate saved.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to update installer candidate.");
    } finally {
      setInstallerCandidateSaving((current) => ({
        ...current,
        [candidate.id]: false,
      }));
    }
  }

  function changeInstallerCandidateDraft<K extends keyof InstallerCandidateDraft>(
    candidateId: string,
    field: K,
    value: InstallerCandidateDraft[K],
  ): void {
    setInstallerCandidateDrafts((current) => {
      const existing = current[candidateId];
      if (!existing) {
        return current;
      }

      return {
        ...current,
        [candidateId]: {
          ...existing,
          [field]: value,
        },
      };
    });
  }

  return (
    <details
      id="installer-candidates"
      className="operations-section operations-disclosure"
    >
      <summary className="operations-disclosure-summary">
        <span>
          <strong>Installer candidates</strong>
          <small>Internal research only</small>
        </span>
      </summary>

      <div className="operations-disclosure-content">
        <div className="operations-section-heading">
          <p className="eyebrow">Installer Research</p>
          <h2>Installer candidates</h2>
          <p>
            Internal research records only. A candidate listed here is not
            approved, recommended, vetted, licensed, insured, partnered, or
            eligible for customer referral. Public installer features remain
            disabled pending legal review.
          </p>
        </div>

        <label className="operations-field operations-customer-search">
          <span>Search candidates</span>
          <input
            type="search"
            placeholder="Business, contact, service area, status…"
            value={installerCandidateSearch}
            onChange={(event) => setInstallerCandidateSearch(event.target.value)}
          />
        </label>

        {privileged ? (
          <div className="operations-customer operations-account-workspace">
            <section className="operations-account-identity">
              <div className="operations-account-section-heading">
                <div>
                  <p className="product-meta">New research lead</p>
                  <h3>Add installer candidate</h3>
                </div>
                <small>Internal only</small>
              </div>
              <div className="operations-product-grid">
                <label className="operations-field"><span>Business name</span><input value={installerCandidateCreateDraft.businessName} onChange={(event) => setInstallerCandidateCreateDraft({ ...installerCandidateCreateDraft, businessName: event.target.value })} /></label>
                <label className="operations-field"><span>Contact name</span><input value={installerCandidateCreateDraft.contactName} onChange={(event) => setInstallerCandidateCreateDraft({ ...installerCandidateCreateDraft, contactName: event.target.value })} /></label>
                <label className="operations-field"><span>Email</span><input type="email" value={installerCandidateCreateDraft.email} onChange={(event) => setInstallerCandidateCreateDraft({ ...installerCandidateCreateDraft, email: event.target.value })} /></label>
                <label className="operations-field"><span>Phone</span><input value={installerCandidateCreateDraft.phone} onChange={(event) => setInstallerCandidateCreateDraft({ ...installerCandidateCreateDraft, phone: event.target.value })} /></label>
                <label className="operations-field"><span>Website</span><input value={installerCandidateCreateDraft.website} onChange={(event) => setInstallerCandidateCreateDraft({ ...installerCandidateCreateDraft, website: event.target.value })} /></label>
                <label className="operations-field"><span>Status</span><select value={installerCandidateCreateDraft.status} onChange={(event) => setInstallerCandidateCreateDraft({ ...installerCandidateCreateDraft, status: event.target.value as InstallerCandidateStatus })}>{INSTALLER_CANDIDATE_STATUSES.map((candidateStatus) => <option key={candidateStatus} value={candidateStatus}>{INSTALLER_CANDIDATE_STATUS_LABELS[candidateStatus]}</option>)}</select></label>
                <label className="operations-field"><span>Service-area notes</span><textarea value={installerCandidateCreateDraft.serviceAreaNotes} onChange={(event) => setInstallerCandidateCreateDraft({ ...installerCandidateCreateDraft, serviceAreaNotes: event.target.value })} /></label>
                <label className="operations-field"><span>Source / provenance</span><textarea value={installerCandidateCreateDraft.sourceReference} onChange={(event) => setInstallerCandidateCreateDraft({ ...installerCandidateCreateDraft, sourceReference: event.target.value })} /></label>
                <label className="operations-field"><span>Internal notes</span><textarea value={installerCandidateCreateDraft.internalNotes} onChange={(event) => setInstallerCandidateCreateDraft({ ...installerCandidateCreateDraft, internalNotes: event.target.value })} /></label>
              </div>
              <button type="button" className="operations-action" disabled={installerCandidateCreating} onClick={() => void addInstallerCandidate()}>{installerCandidateCreating ? "Saving…" : "Add candidate"}</button>
            </section>
          </div>
        ) : (
          <p className="operations-note">
            Installer research is read-only for Employee and legacy Manager roles.
          </p>
        )}

        {filteredInstallerCandidates.length === 0 ? (
          <p className="account-muted">No installer candidates match this view.</p>
        ) : (
          <div className="operations-customer-list">
            {filteredInstallerCandidates.map((candidate) => {
              const draft = installerCandidateDrafts[candidate.id] ?? installerCandidateDraft(candidate);
              const saving = installerCandidateSaving[candidate.id] === true;
              return (
                <article key={candidate.id} className="operations-customer operations-account-workspace">
                  <section className="operations-account-identity">
                    <div className="operations-account-heading">
                      <div>
                        <p className="product-meta">Potential installer candidate</p>
                        <h3>{candidate.business_name}</h3>
                      </div>
                      <span className="operations-account-status">{INSTALLER_CANDIDATE_STATUS_LABELS[candidate.status]}</span>
                    </div>

                    <div className="operations-product-grid">
                      <label className="operations-field"><span>Business name</span><input disabled={!privileged} value={draft.businessName} onChange={(event) => changeInstallerCandidateDraft(candidate.id, "businessName", event.target.value)} /></label>
                      <label className="operations-field"><span>Contact name</span><input disabled={!privileged} value={draft.contactName} onChange={(event) => changeInstallerCandidateDraft(candidate.id, "contactName", event.target.value)} /></label>
                      <label className="operations-field"><span>Email</span><input type="email" disabled={!privileged} value={draft.email} onChange={(event) => changeInstallerCandidateDraft(candidate.id, "email", event.target.value)} /></label>
                      <label className="operations-field"><span>Phone</span><input disabled={!privileged} value={draft.phone} onChange={(event) => changeInstallerCandidateDraft(candidate.id, "phone", event.target.value)} /></label>
                      <label className="operations-field"><span>Website</span><input disabled={!privileged} value={draft.website} onChange={(event) => changeInstallerCandidateDraft(candidate.id, "website", event.target.value)} /></label>
                      <label className="operations-field"><span>Status</span><select disabled={!privileged} value={draft.status} onChange={(event) => changeInstallerCandidateDraft(candidate.id, "status", event.target.value as InstallerCandidateStatus)}>{INSTALLER_CANDIDATE_STATUSES.map((candidateStatus) => <option key={candidateStatus} value={candidateStatus}>{INSTALLER_CANDIDATE_STATUS_LABELS[candidateStatus]}</option>)}</select></label>
                      <label className="operations-field"><span>Service-area notes</span><textarea disabled={!privileged} value={draft.serviceAreaNotes} onChange={(event) => changeInstallerCandidateDraft(candidate.id, "serviceAreaNotes", event.target.value)} /></label>
                      <label className="operations-field"><span>Source / provenance</span><textarea disabled={!privileged} value={draft.sourceReference} onChange={(event) => changeInstallerCandidateDraft(candidate.id, "sourceReference", event.target.value)} /></label>
                      <label className="operations-field"><span>Internal notes</span><textarea disabled={!privileged} value={draft.internalNotes} onChange={(event) => changeInstallerCandidateDraft(candidate.id, "internalNotes", event.target.value)} /></label>
                    </div>

                    <p className="operations-governance-context">
                      Updated {new Date(candidate.updated_at).toLocaleString()} · internal research only
                    </p>
                    {privileged ? (
                      <button type="button" className="operations-action secondary" disabled={saving} onClick={() => void saveInstallerCandidate(candidate)}>{saving ? "Saving…" : "Save candidate"}</button>
                    ) : null}
                  </section>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </details>
  );
}
