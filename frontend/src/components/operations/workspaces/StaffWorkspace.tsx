/**
 * Staff workspace: Operations user access and roles (administrator and
 * developer roles only).
 *
 * Data:    src/api/administration.ts
 *            getAdministrationAccounts()   -> GET /api/administration/accounts
 *            updateAdministrationRoles()   -> PUT /api/administration/accounts/{id}/roles
 *            updateAdministrationStatus()  -> PUT /api/administration/accounts/{id}/status
 *          (backend/app/api/administration.py)
 * Tests:   backend/tests/test_account_administration.py,
 *          test_account_status_administration.py, test_administration_schemas.py
 * Shown by OperationsPage.tsx only to administrators and developers.
 * Loads the account list when its disclosure is first opened.
 */
import { useMemo, useState } from "react";

import {
  getAdministrationAccounts,
  updateAdministrationRoles,
  updateAdministrationStatus,
  type AdministrationAccount,
  type WebManagedRole,
} from "../../../api/administration";
import type { OperationsNoticeProps, SaveState } from "../operationsShared";

const WEB_MANAGED_ROLES: WebManagedRole[] = [
  "employee",
  "manager",
  "administrator",
];

type AssignableWebRole = Exclude<WebManagedRole, "manager">;

const WEB_ASSIGNABLE_ROLES: AssignableWebRole[] = [
  "employee",
  "administrator",
];

const STAFF_ACCESS_DESCRIPTIONS: Record<AssignableWebRole, string> = {
  employee: "Operations access for day-to-day staff work.",
  administrator: "Privileged Operations access, including user administration.",
};

function roleLabel(role: string): string {
  return role.charAt(0).toUpperCase() + role.slice(1);
}

function lockedSelfAdminText(
  ownAccount: boolean,
  roles: WebManagedRole[],
): string {
  if (
    ownAccount
    && roles.includes("administrator")
  ) {
    return "Your own administrator role is protected from removal.";
  }

  return (
    "Customer access is preserved automatically. "
    + "Role changes are audited."
  );
}

type StaffWorkspaceProps = OperationsNoticeProps & {
  /** The signed-in operator, so their own administrator role is protected. */
  currentUserEmail: string | null;
};

export function StaffWorkspace({
  currentUserEmail,
  onMessage: setMessage,
  onError: setError,
}: StaffWorkspaceProps) {
  const [administrationAccounts, setAdministrationAccounts] =
    useState<AdministrationAccount[]>([]);
  const [administrationSearch, setAdministrationSearch] =
    useState("");
  const [administrationLoaded, setAdministrationLoaded] =
    useState(false);
  const [administrationLoading, setAdministrationLoading] =
    useState(false);
  const [administrationError, setAdministrationError] =
    useState<string | null>(null);
  const [administrationRoleDrafts, setAdministrationRoleDrafts] =
    useState<Record<string, WebManagedRole[]>>({});
  const [administrationSaveStates, setAdministrationSaveStates] =
    useState<Record<string, SaveState>>({});
  const [administrationStatusSaveStates, setAdministrationStatusSaveStates] =
    useState<Record<string, SaveState>>({});

  async function loadAdministrationAccounts(): Promise<void> {
    if (
      administrationLoaded
      || administrationLoading
    ) {
      return;
    }

    setAdministrationLoading(true);
    setAdministrationError(null);

    try {
      const result =
        await getAdministrationAccounts();

      setAdministrationAccounts(result);
      setAdministrationRoleDrafts(
        Object.fromEntries(
          result.map((account) => [
            account.id,
            WEB_MANAGED_ROLES.filter(
              (role) => account.roles.includes(role),
            ),
          ]),
        ),
      );
      setAdministrationLoaded(true);
    } catch (caught) {
      setAdministrationError(
        caught instanceof Error
          ? caught.message
          : "Unable to load user accounts.",
      );
    } finally {
      setAdministrationLoading(false);
    }
  }

  const filteredAdministrationAccounts = useMemo(() => {
    const query =
      administrationSearch.trim().toLowerCase();

    if (query.length === 0) {
      return administrationAccounts;
    }

    return administrationAccounts.filter((account) => {
      const searchable = [
        account.email,
        account.status,
        ...account.roles,
        account.email_verified ? "verified" : "unverified",
        account.mfa_enrolled ? "mfa enrolled" : "mfa not enrolled",
      ]
        .join(" ")
        .toLowerCase();

      return searchable.includes(query);
    });
  }, [
    administrationAccounts,
    administrationSearch,
  ]);

  function selectAdministrationRole(
    accountId: string,
    role: AssignableWebRole | null,
  ): void {
    setAdministrationRoleDrafts((current) => ({
      ...current,
      [accountId]: role === null ? [] : [role],
    }));
  }

  async function saveAdministrationRoles(
    account: AdministrationAccount,
  ): Promise<void> {
    const desiredRoles =
      administrationRoleDrafts[account.id] ?? [];

    setAdministrationError(null);
    setMessage(null);
    setAdministrationSaveStates((current) => ({
      ...current,
      [account.id]: "saving",
    }));

    try {
      const updated = await updateAdministrationRoles(
        account.id,
        desiredRoles,
      );

      setAdministrationAccounts((current) =>
        current.map((candidate) =>
          candidate.id === updated.id
            ? updated
            : candidate,
        ),
      );

      setAdministrationRoleDrafts((current) => ({
        ...current,
        [updated.id]: WEB_MANAGED_ROLES.filter(
          (role) => updated.roles.includes(role),
        ),
      }));

      setMessage(
        `Access roles saved for ${updated.email}.`,
      );
      setAdministrationSaveStates((current) => ({
        ...current,
        [account.id]: "saved",
      }));

      window.setTimeout(() => {
        setAdministrationSaveStates((current) => ({
          ...current,
          [account.id]: "idle",
        }));
      }, 1800);
    } catch (caught) {
      setAdministrationSaveStates((current) => ({
        ...current,
        [account.id]: "idle",
      }));
      setAdministrationError(
        caught instanceof Error
          ? caught.message
          : "Account role update failed.",
      );
    }
  }

  async function saveAdministrationStatus(
    account: AdministrationAccount,
    nextStatus: "active" | "disabled",
  ): Promise<void> {
    setAdministrationError(null);
    setMessage(null);
    setAdministrationStatusSaveStates((current) => ({
      ...current,
      [account.id]: "saving",
    }));

    try {
      const updated = await updateAdministrationStatus(
        account.id,
        nextStatus,
      );

      setAdministrationAccounts((current) =>
        current.map((candidate) =>
          candidate.id === updated.id
            ? updated
            : candidate,
        ),
      );

      setMessage(
        nextStatus === "disabled"
          ? `Account disabled for ${updated.email}. Existing sessions were revoked.`
          : `Account re-enabled for ${updated.email}.`,
      );
      setAdministrationStatusSaveStates((current) => ({
        ...current,
        [account.id]: "saved",
      }));

      window.setTimeout(() => {
        setAdministrationStatusSaveStates((current) => ({
          ...current,
          [account.id]: "idle",
        }));
      }, 1800);
    } catch (caught) {
      setAdministrationStatusSaveStates((current) => ({
        ...current,
        [account.id]: "idle",
      }));
      setAdministrationError(
        caught instanceof Error
          ? caught.message
          : "Account status update failed.",
      );
    }
  }

  return (
    <details
      id="account-administration"
      className="operations-section operations-disclosure"
      onToggle={(event) => {
        if (
          event.currentTarget.open
          && !administrationLoaded
        ) {
          void loadAdministrationAccounts();
        }
      }}
    >
      <summary className="operations-disclosure-summary">
        <span>
          <strong>User access &amp; roles</strong>
          <small>Administrator account management</small>
        </span>
      </summary>

      <div className="operations-disclosure-content">
        <div className="operations-section-heading">
          <p className="eyebrow">Account Administration</p>
          <h2>User access &amp; roles</h2>
          <p>
            Customer registration remains self-service. Employee,
            manager, and administrator access is granted here.
            Developer access remains local-only.
          </p>
        </div>

        {administrationLoading ? (
          <p className="account-muted">
            Loading user accounts…
          </p>
        ) : administrationError !== null ? (
          <p
            className="operations-alert operations-error"
            role="alert"
          >
            {administrationError}
          </p>
        ) : (
          <>
            <label
              className={
                "operations-field "
                + "operations-customer-search"
              }
            >
              <span>Search user accounts</span>
              <input
                type="search"
                placeholder="Email, status, role…"
                value={administrationSearch}
                onChange={(event) => {
                  setAdministrationSearch(
                    event.target.value,
                  );
                }}
              />
            </label>

            {administrationAccounts.length === 0 ? (
              <p className="account-muted">
                No persisted user accounts.
              </p>
            ) : filteredAdministrationAccounts.length === 0 ? (
              <p className="account-muted">
                No accounts match this search.
              </p>
            ) : (
              <div className="operations-customer-list">
                {filteredAdministrationAccounts.map((account) => {
                  const roleDraft =
                    administrationRoleDrafts[account.id]
                    ?? [];
                  const developerManaged =
                    account.roles.includes("developer");
                  const ownAccount = (
                    currentUserEmail !== null
                    && account.email.toLowerCase()
                      === currentUserEmail.toLowerCase()
                  );
                  const saveState =
                    administrationSaveStates[account.id]
                    ?? "idle";
                  const statusSaveState =
                    administrationStatusSaveStates[account.id]
                    ?? "idle";

                  return (
                    <article
                      key={account.id}
                      className="operations-customer"
                      data-account-status={account.status}
                    >
                      <header>
                        <div>
                          <p className="product-meta">
                            Account · {account.status}
                          </p>
                          <h3>{account.email}</h3>
                          <small>
                            Created{" "}
                            {new Date(
                              account.created_at,
                            ).toLocaleString()}
                            {account.last_login_at !== null
                              ? ` · Last login ${new Date(
                                  account.last_login_at,
                                ).toLocaleString()}`
                              : " · Never logged in"}
                          </small>
                        </div>
                      </header>

                      <div className="operations-governance-badges">
                        <span>Status: {roleLabel(account.status)}</span>
                        <span>Email: {account.email_verified ? "verified" : "unverified"}</span>
                        <span>
                          MFA: {account.mfa_required
                            ? account.mfa_enrolled
                              ? "required · enrolled"
                              : "required · pending"
                            : "not required"}
                        </span>
                        <span>
                          Access: {account.roles.length > 0
                            ? account.roles.map(roleLabel).join(", ")
                            : "none"}
                        </span>
                      </div>

                      <div className="operations-address-list operations-access-grid">
                        <div className="operations-address">
                          <strong>Identity</strong>
                          <address>
                            Email {account.email_verified
                              ? "verified"
                              : "not verified"}
                            <br />
                            MFA {account.mfa_required
                              ? account.mfa_enrolled
                                ? "required · enrolled"
                                : "required · enrollment pending"
                              : "not required"}
                          </address>
                          <small>
                            Persisted roles:{" "}
                            {account.roles.length > 0
                              ? account.roles.join(", ")
                              : "none"}
                          </small>

                          <div className="operations-account-status-actions">
                            {account.roles.includes("developer") ? (
                              <small>
                                Developer account status is managed locally.
                              </small>
                            ) : ownAccount ? (
                              <small>
                                Your current account cannot disable itself.
                              </small>
                            ) : account.status === "locked" ? (
                              <small>
                                This account is temporarily controlled by the
                                login lockout workflow.
                              </small>
                            ) : (
                              <>
                                <button
                                  type="button"
                                  className="operations-action secondary"
                                  disabled={
                                    statusSaveState === "saving"
                                    || saveState === "saving"
                                  }
                                  onClick={() => {
                                    const nextStatus = account.status === "disabled"
                                      ? "active"
                                      : "disabled";
                                    const confirmed = nextStatus === "active"
                                      || window.confirm(
                                        `Disable ${account.email}? Sign-in will be blocked and active sessions will be revoked. Historical records and roles will be preserved.`,
                                      );

                                    if (confirmed) {
                                      void saveAdministrationStatus(
                                        account,
                                        nextStatus,
                                      );
                                    }
                                  }}
                                >
                                  {statusSaveState === "saving"
                                    ? "Saving…"
                                    : account.status === "disabled"
                                      ? "Re-enable account"
                                      : "Disable account"}
                                </button>
                                <small>
                                  Disabling preserves history and role assignments
                                  while blocking sign-in.
                                </small>
                              </>
                            )}
                          </div>
                        </div>

                        <div className="operations-address operations-role-editor">
                          <strong>Staff access level</strong>

                          {developerManaged ? (
                            <div className="operations-role-managed-note">
                              <strong>Developer</strong>
                              <p>
                                Highest-privilege application access.
                              </p>
                              <small>
                                Developer access is provisioned and revoked through
                                local administrative tooling, not the web console.
                                Administrators and developers can assign Employee or
                                Administrator access to ordinary accounts here.
                              </small>
                            </div>
                          ) : (
                            <>
                              {roleDraft.includes("manager") ? (
                                <div className="operations-role-legacy-note">
                                  <strong>Manager · legacy assignment</strong>
                                  <small>
                                    Manager cannot be newly assigned. Choose Employee,
                                    Administrator, or No staff access to replace this
                                    legacy role.
                                  </small>
                                </div>
                              ) : null}

                              <div
                                className="operations-role-options"
                                role="radiogroup"
                                aria-label={`Staff access level for ${account.email}`}
                              >
                                <label className="operations-role-option">
                                  <input
                                    type="radio"
                                    name={`staff-access-${account.id}`}
                                    checked={roleDraft.length === 0}
                                    disabled={
                                      (
                                        ownAccount
                                        && account.roles.includes("administrator")
                                      )
                                      || saveState === "saving"
                                      || statusSaveState === "saving"
                                    }
                                    onChange={() => {
                                      selectAdministrationRole(
                                        account.id,
                                        null,
                                      );
                                    }}
                                  />
                                  <span className="operations-role-option-copy">
                                    <strong>No staff access</strong>
                                    <small>
                                      Customer access is retained without Operations
                                      permissions.
                                    </small>
                                  </span>
                                </label>

                                {WEB_ASSIGNABLE_ROLES.map((role) => {
                                  const lockedSelfAdmin = (
                                    ownAccount
                                    && account.roles.includes("administrator")
                                    && role !== "administrator"
                                  );

                                  return (
                                    <label
                                      key={role}
                                      className="operations-role-option"
                                    >
                                      <input
                                        type="radio"
                                        name={`staff-access-${account.id}`}
                                        checked={roleDraft.includes(role)}
                                        disabled={
                                          lockedSelfAdmin
                                          || saveState === "saving"
                                          || statusSaveState === "saving"
                                        }
                                        onChange={() => {
                                          selectAdministrationRole(
                                            account.id,
                                            role,
                                          );
                                        }}
                                      />
                                      <span className="operations-role-option-copy">
                                        <strong>{roleLabel(role)}</strong>
                                        <small>
                                          {STAFF_ACCESS_DESCRIPTIONS[role]}
                                        </small>
                                      </span>
                                    </label>
                                  );
                                })}
                              </div>

                              <button
                                type="button"
                                className={
                                  "operations-action secondary operations-role-save "
                                  + (
                                    saveState === "saved"
                                      ? "is-saved"
                                      : ""
                                  )
                                }
                                disabled={
                                  roleDraft.includes("manager")
                                  || saveState === "saving"
                                  || statusSaveState === "saving"
                                }
                                onClick={() => {
                                  void saveAdministrationRoles(account);
                                }}
                              >
                                {saveState === "saving"
                                  ? "Saving…"
                                  : saveState === "saved"
                                    ? "Saved ✓"
                                    : "Save access level"}
                              </button>

                              <small className="operations-role-helper">
                                {roleDraft.includes("manager")
                                  ? (
                                      "Select a replacement level before saving. "
                                      + "The legacy Manager role cannot be re-saved."
                                    )
                                  : lockedSelfAdminText(
                                      ownAccount,
                                      roleDraft,
                                    )}
                              </small>
                            </>
                          )}
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </>
        )}
      </div>
    </details>
  );
}
