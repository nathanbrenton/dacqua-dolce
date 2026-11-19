// Account & security panel: email verification, password and authenticator
// (MFA) reconfiguration. Shown to every signed-in account, staff included.
//
// API: requestEmailVerification, reconfigureMfa in api/authentication.ts

import { type FormEvent, useState } from "react";
import {
  type AuthenticationStatus,
  reconfigureMfa,
  requestEmailVerification,
} from "../../api/authentication";
import { PasswordInput } from "../forms/PasswordInput";

const PRIVILEGED_MFA_ROLES = new Set([
  "manager",
  "administrator",
  "developer",
]);

function hasPrivilegedMfaRole(
  account: AuthenticationStatus,
): boolean {
  return account.roles.some((role) =>
    PRIVILEGED_MFA_ROLES.has(role),
  );
}

type SecurityPanelProps = {
  account: AuthenticationStatus;
  onMfaReconfigurationStarted: (
    account: AuthenticationStatus,
  ) => void;
};

export function SecurityPanel({
  account,
  onMfaReconfigurationStarted,
}: SecurityPanelProps) {
  const [password, setPassword] =
    useState("");

  const [reconfiguring, setReconfiguring] =
    useState(false);

  const [securityError, setSecurityError] =
    useState<string | null>(null);

  const [
    verificationSending,
    setVerificationSending,
  ] = useState(false);

  const [
    verificationMessage,
    setVerificationMessage,
  ] = useState<string | null>(null);

  const privileged =
    hasPrivilegedMfaRole(account);

  async function resendVerification() {
    setSecurityError(null);
    setVerificationMessage(null);
    setVerificationSending(true);

    try {
      const message =
        await requestEmailVerification();

      setVerificationMessage(
        message,
      );
    } catch (caught) {
      setSecurityError(
        caught instanceof Error
          ? caught.message
          : (
              "Unable to request "
              + "verification email."
            ),
      );
    } finally {
      setVerificationSending(false);
    }
  }

  async function replaceAuthenticator(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setSecurityError(null);
    setReconfiguring(true);

    try {
      const pendingAccount =
        await reconfigureMfa(
          password,
        );

      setPassword("");

      onMfaReconfigurationStarted(
        pendingAccount,
      );
    } catch (caught) {
      setSecurityError(
        caught instanceof Error
          ? caught.message
          : (
              "Unable to replace "
              + "authenticator."
            ),
      );
    } finally {
      setReconfiguring(false);
    }
  }

  return (
    <section className="account-panel">
      <h2>Security</h2>

      <div className="account-security-status">
        <div>
          <strong>Email address</strong>

          <p className="account-security-email">
            {account.email}
          </p>
        </div>

        <span
          className={
            account.email_verified
              ? "account-security-verified"
              : "account-security-unverified"
          }
        >
          {account.email_verified
            ? "Verified"
            : "Not verified"}
        </span>
      </div>

      {!account.email_verified ? (
        <div
          className={
            "account-email-verification-actions"
          }
        >
          <p className="account-muted">
            Verify this email before
            production account access is
            granted.
          </p>

          <button
            type="button"
            className="account-action"
            disabled={verificationSending}
            onClick={() => {
              void resendVerification();
            }}
          >
            {verificationSending
              ? "Sending..."
              : "Resend Verification Email"}
          </button>

          {verificationMessage !== null ? (
            <p
              className="account-success-inline"
              role="status"
            >
              {verificationMessage}
            </p>
          ) : null}
        </div>
      ) : null}

      <div className="account-security-status">
        <div className="account-security-authenticator">
          <div
            className={
              "authenticator-generic-icon "
              + "account-authenticator-icon"
            }
            aria-hidden="true"
          >
            <span
              className="authenticator-phone"
            />
            <span
              className="authenticator-shield"
            >
              ✓
            </span>
          </div>

          <div>
            <strong>
              Authenticator MFA
            </strong>

            {privileged ? (
              <div
                className={
                  "authenticator-compatibility-meta"
                }
              >
                <span
                  className={
                    "authenticator-compatibility-badge"
                  }
                >
                  Microsoft Authenticator
                  compatible
                </span>

                <span>
                  Standard TOTP
                </span>
              </div>
            ) : null}
          </div>
        </div>

        <span>
          {privileged
            ? "Enabled"
            : account.roles.includes(
                "customer",
              )
              ? "Optional"
              : "Not required"}
        </span>
      </div>

      {privileged ? (
        <>
          <p className="account-muted">
            Protects privileged Operations
            access. Works with Microsoft
            Authenticator and other
            standards-compatible TOTP
            authenticator apps.
          </p>

          <details
            className="account-security-replace"
          >
            <summary>
              Replace authenticator
            </summary>

            <p className="account-muted">
              Replacing the authenticator
              immediately invalidates the
              existing setup and recovery
              codes, signs out other
              sessions, and requires a
              new enrollment.
            </p>

            <form
              className="account-form"
              onSubmit={(event) => {
                void replaceAuthenticator(
                  event,
                );
              }}
            >
              <PasswordInput
                label="Current password"
                autoComplete="current-password"
                required
                maxLength={256}
                value={password}
                onChange={(event) => {
                  setPassword(
                    event.target.value,
                  );
                }}
              />

              {securityError !== null ? (
                <p
                  className="account-error-inline"
                  role="alert"
                >
                  {securityError}
                </p>
              ) : null}

              <button
                type="submit"
                className="account-action"
                disabled={reconfiguring}
              >
                {reconfiguring
                  ? "Replacing..."
                  : "Replace Authenticator"}
              </button>
            </form>
          </details>
        </>
      ) : account.roles.includes(
        "customer",
      ) ? (
        <p className="account-muted">
          Authenticator MFA is optional
          for customer accounts. Enable
          it for additional account
          security.
        </p>
      ) : (
        <p className="account-muted">
          Authenticator MFA is not
          required for this account.
        </p>
      )}
    </section>
  );
}
