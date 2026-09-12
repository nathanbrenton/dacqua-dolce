import {
  type FormEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  QRCodeSVG,
} from "qrcode.react";

import {
  enrollMfa,
  loginAccount,
  registerAccount,
  verifyMfa,
  type AuthenticationStatus,
  type MfaEnrollmentResponse,
} from "../../api/authentication";

type AuthMode = "login" | "register";

type AuthStage =
  | "credentials"
  | "mfa-enroll"
  | "mfa-verify";

const EMAIL_PATTERN =
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type AuthDialogProps = {
  open: boolean;
  pendingAuthentication:
    AuthenticationStatus | null;
  onClose: () => void;
  onAuthenticated: (
    account: AuthenticationStatus,
  ) => void;
  onAuthenticationPending: (
    account: AuthenticationStatus,
  ) => void;
  onCancelPendingAuthentication:
    () => void;
  onForgotPassword: () => void;
};

export function AuthDialog({
  open,
  pendingAuthentication,
  onClose,
  onAuthenticated,
  onAuthenticationPending,
  onCancelPendingAuthentication,
  onForgotPassword,
}: AuthDialogProps) {
  const dialogRef =
    useRef<HTMLDialogElement>(null);

  const [mode, setMode] =
    useState<AuthMode>("login");

  const [stage, setStage] =
    useState<AuthStage>(
      "credentials",
    );

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [mfaCode, setMfaCode] =
    useState("");

  const [
    enrollment,
    setEnrollment,
  ] = useState<
    MfaEnrollmentResponse | null
  >(null);

  const [error, setError] =
    useState<string | null>(null);

  const [submitting, setSubmitting] =
    useState(false);

  useEffect(() => {
    const dialog = dialogRef.current;

    if (dialog === null) {
      return;
    }

    if (open && !dialog.open) {
      dialog.showModal();
    }

    if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  useEffect(() => {
    if (!open) {
      return;
    }

    setError(null);
    setPassword("");
    setMfaCode("");

    if (
      pendingAuthentication?.email
      !== null
      && pendingAuthentication?.email
      !== undefined
    ) {
      setEmail(
        pendingAuthentication.email,
      );
    }

    if (
      pendingAuthentication
        ?.mfa_enrollment_required
    ) {
      setStage("mfa-enroll");
      return;
    }

    if (
      pendingAuthentication
        ?.mfa_required
    ) {
      setStage("mfa-verify");
      return;
    }

    setStage("credentials");
    setEnrollment(null);
  }, [
    open,
    pendingAuthentication,
  ]);

  function switchMode(
    nextMode: AuthMode,
  ) {
    setMode(nextMode);
    setError(null);
    setPassword("");
  }

  function finishAuthentication(
    account: AuthenticationStatus,
  ) {
    if (!account.authenticated) {
      setError(
        "Authentication could not be completed.",
      );
      return;
    }

    onAuthenticated(account);

    setPassword("");
    setMfaCode("");
    setEnrollment(null);
    setStage("credentials");

    onClose();
  }

  function handlePendingAuthentication(
    account: AuthenticationStatus,
  ) {
    onAuthenticationPending(
      account,
    );

    setPassword("");
    setMfaCode("");
    setError(null);

    if (
      account.mfa_enrollment_required
    ) {
      setStage("mfa-enroll");
      return;
    }

    if (account.mfa_required) {
      setStage("mfa-verify");
      return;
    }

    setError(
      "Authentication could not be completed.",
    );
  }

  async function handleCredentials(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setError(null);

    const normalizedEmail =
      email.trim().toLowerCase();

    if (
      !EMAIL_PATTERN.test(
        normalizedEmail,
      )
    ) {
      setError(
        "Enter a valid email address.",
      );
      return;
    }

    setSubmitting(true);

    try {
      const account = await (
        mode === "login"
          ? loginAccount({
              email: normalizedEmail,
              password,
            })
          : registerAccount({
              email: normalizedEmail,
              password,
            })
      );

      if (account.authenticated) {
        finishAuthentication(
          account,
        );
      } else {
        handlePendingAuthentication(
          account,
        );
      }
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Authentication failed.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function startEnrollment() {
    setError(null);
    setSubmitting(true);

    try {
      const result =
        await enrollMfa();

      setEnrollment(result);
      setMfaCode("");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : (
              "Unable to begin "
              + "MFA enrollment."
            ),
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleMfaVerification(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setError(null);

    const normalizedCode =
      mfaCode.trim();

    if (normalizedCode.length < 6) {
      setError(
        "Enter your authenticator or recovery code.",
      );
      return;
    }

    setSubmitting(true);

    try {
      const account =
        await verifyMfa(
          normalizedCode,
        );

      finishAuthentication(
        account,
      );
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "MFA verification failed.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  function requestClose() {
    if (
      stage !== "credentials"
      || pendingAuthentication
        !== null
    ) {
      onCancelPendingAuthentication();
      return;
    }

    onClose();
  }

  const dialogTitle =
    stage === "mfa-enroll"
      ? "Secure your account."
      : stage === "mfa-verify"
        ? "Verify it’s you."
        : mode === "login"
          ? "Welcome back."
          : "Create your account.";

  return (
    <dialog
      ref={dialogRef}
      className="auth-dialog"
      aria-labelledby="auth-dialog-title"
      onClose={onClose}
      onCancel={(event) => {
        event.preventDefault();
        requestClose();
      }}
    >
      <div className="auth-dialog-header">
        <div>
          <p className="auth-kicker">
            D&apos;Acqua Dolce
          </p>

          <h2 id="auth-dialog-title">
            {dialogTitle}
          </h2>
        </div>

        <button
          className="auth-close"
          type="button"
          aria-label="Close authentication dialog"
          onClick={requestClose}
        >
          ×
        </button>
      </div>

      {stage === "credentials" ? (
        <>
          <div
            className="auth-mode-switch"
            aria-label="Authentication mode"
          >
            <button
              type="button"
              className={
                mode === "login"
                  ? "is-active"
                  : undefined
              }
              aria-pressed={
                mode === "login"
              }
              onClick={() => {
                switchMode("login");
              }}
            >
              Sign In
            </button>

            <button
              type="button"
              className={
                mode === "register"
                  ? "is-active"
                  : undefined
              }
              aria-pressed={
                mode === "register"
              }
              onClick={() => {
                switchMode(
                  "register",
                );
              }}
            >
              Create Account
            </button>
          </div>

          <form
            className="auth-form"
            onSubmit={(event) => {
              void handleCredentials(
                event,
              );
            }}
          >
            <label>
              <span>Email address</span>

              <input
                type="email"
                name="email"
                autoComplete="email"
                required
                maxLength={320}
                value={email}
                onChange={(event) => {
                  setEmail(
                    event.target.value,
                  );
                }}
              />
            </label>

            <label>
              <span>Password</span>

              <input
                type="password"
                name="password"
                autoComplete={
                  mode === "login"
                    ? "current-password"
                    : "new-password"
                }
                required
                minLength={
                  mode === "register"
                    ? 12
                    : 1
                }
                maxLength={256}
                value={password}
                onChange={(event) => {
                  setPassword(
                    event.target.value,
                  );
                }}
              />
            </label>

            {mode === "register" ? (
              <p className="auth-helper">
                Use at least 12 characters.
              </p>
            ) : (
              <button
                type="button"
                className="auth-forgot-link"
                onClick={() => {
                  onClose();
                  onForgotPassword();
                }}
              >
                Forgot password?
              </button>
            )}

            {error !== null ? (
              <p
                className="auth-error"
                role="alert"
              >
                {error}
              </p>
            ) : null}

            <button
              className="auth-submit"
              type="submit"
              disabled={submitting}
            >
              {submitting
                ? "Working..."
                : mode === "login"
                  ? "Sign In"
                  : "Create Account"}
            </button>
          </form>
        </>
      ) : null}

      {stage === "mfa-enroll" ? (
        <div className="auth-mfa-panel">
          <p className="auth-helper">
            Privileged accounts require
            an authenticator before
            Operations access is granted.
          </p>

          {enrollment === null ? (
            <button
              className="auth-submit"
              type="button"
              disabled={submitting}
              onClick={() => {
                void startEnrollment();
              }}
            >
              {submitting
                ? "Preparing..."
                : "Set Up Authenticator"}
            </button>
          ) : (
            <>
              <div className="auth-mfa-step">
                <p className="auth-mfa-label">
                  1. Scan with your
                  authenticator app
                </p>

                <p className="auth-helper">
                  Open your authenticator
                  app and scan this QR
                  code.
                </p>

                <p className="auth-helper">
                  Microsoft Authenticator:
                  choose Add account,
                  then Other account,
                  then Scan a QR code.
                  Do not choose Personal
                  account or Work or
                  school account.
                </p>

                <div
                  className="auth-mfa-qr"
                  aria-label={
                    "Authenticator "
                    + "setup QR code"
                  }
                >
                  <QRCodeSVG
                    value={
                      enrollment
                        .provisioning_uri
                    }
                    size={220}
                    level="M"
                    marginSize={2}
                    title={
                      "D'Acqua Dolce "
                      + "authenticator setup"
                    }
                  />
                </div>

                <details
                  className={
                    "auth-mfa-manual"
                  }
                >
                  <summary>
                    Can&apos;t scan?
                    Enter setup key
                    manually
                  </summary>

                  <p className="auth-helper">
                    Choose a time-based
                    authenticator account
                    and enter this key:
                  </p>

                  <code
                    className={
                      "auth-mfa-secret"
                    }
                  >
                    {enrollment.secret}
                  </code>
                </details>
              </div>

              <div className="auth-mfa-step">
                <p className="auth-mfa-label">
                  2. Save your recovery
                  codes
                </p>

                <p className="auth-helper">
                  Store these somewhere
                  secure. Each code works
                  once, and they will not
                  be shown again after
                  enrollment is complete.
                </p>

                <div
                  className="auth-recovery-codes"
                  aria-label="MFA recovery codes"
                >
                  {enrollment
                    .recovery_codes
                    .map((code) => (
                      <code key={code}>
                        {code}
                      </code>
                    ))}
                </div>
              </div>

              <form
                className="auth-mfa-form"
                onSubmit={(event) => {
                  void handleMfaVerification(
                    event,
                  );
                }}
              >
                <label>
                  <span>
                    3. Enter the
                    6-digit code
                  </span>

                  <input
                    type="text"
                    name="mfa-code"
                    autoComplete="one-time-code"
                    inputMode="numeric"
                    required
                    maxLength={64}
                    value={mfaCode}
                    onChange={(event) => {
                      setMfaCode(
                        event.target.value,
                      );
                    }}
                  />
                </label>

                {error !== null ? (
                  <p
                    className="auth-error"
                    role="alert"
                  >
                    {error}
                  </p>
                ) : null}

                <button
                  className="auth-submit"
                  type="submit"
                  disabled={submitting}
                >
                  {submitting
                    ? "Verifying..."
                    : "Enable MFA"}
                </button>
              </form>
            </>
          )}

          {error !== null
          && enrollment === null ? (
            <p
              className="auth-error"
              role="alert"
            >
              {error}
            </p>
          ) : null}
        </div>
      ) : null}

      {stage === "mfa-verify" ? (
        <form
          className="auth-form"
          onSubmit={(event) => {
            void handleMfaVerification(
              event,
            );
          }}
        >
          <p className="auth-helper">
            Enter the current code from
            your authenticator app. A
            one-time recovery code also
            works.
          </p>

          <label>
            <span>
              Authenticator or recovery
              code
            </span>

            <input
              type="text"
              name="mfa-code"
              autoComplete="one-time-code"
              required
              maxLength={64}
              autoFocus
              value={mfaCode}
              onChange={(event) => {
                setMfaCode(
                  event.target.value,
                );
              }}
            />
          </label>

          {error !== null ? (
            <p
              className="auth-error"
              role="alert"
            >
              {error}
            </p>
          ) : null}

          <button
            className="auth-submit"
            type="submit"
            disabled={submitting}
          >
            {submitting
              ? "Verifying..."
              : "Verify"}
          </button>
        </form>
      ) : null}

      <p className="auth-privacy-note">
        {stage === "credentials"
          ? (
              "Your session is stored "
              + "in a secure, HTTP-only "
              + "cookie."
            )
          : (
              "Privileged access remains "
              + "locked until MFA "
              + "verification succeeds."
            )}
      </p>
    </dialog>
  );
}
