import {
  type FormEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  loginAccount,
  registerAccount,
  type AuthenticationStatus,
} from "../../api/authentication";

type AuthMode = "login" | "register";

const EMAIL_PATTERN =
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type AuthDialogProps = {
  open: boolean;
  onClose: () => void;
  onAuthenticated: (
    account: AuthenticationStatus,
  ) => void;
  onForgotPassword: () => void;
};

export function AuthDialog({
  open,
  onClose,
  onAuthenticated,
  onForgotPassword,
}: AuthDialogProps) {
  const dialogRef =
    useRef<HTMLDialogElement>(null);

  const [mode, setMode] =
    useState<AuthMode>("login");

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

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
    if (open) {
      setError(null);
      setPassword("");
    }
  }, [open]);

  function switchMode(
    nextMode: AuthMode,
  ) {
    setMode(nextMode);
    setError(null);
    setPassword("");
  }

  async function handleSubmit(
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

      onAuthenticated(account);
      setPassword("");
      onClose();
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

  return (
    <dialog
      ref={dialogRef}
      className="auth-dialog"
      aria-labelledby="auth-dialog-title"
      onClose={onClose}
      onCancel={onClose}
    >
      <div className="auth-dialog-header">
        <div>
          <p className="auth-kicker">
            D&apos;Acqua Dolce
          </p>

          <h2 id="auth-dialog-title">
            {mode === "login"
              ? "Welcome back."
              : "Create your account."}
          </h2>
        </div>

        <button
          className="auth-close"
          type="button"
          aria-label="Close authentication dialog"
          onClick={onClose}
        >
          ×
        </button>
      </div>

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
              "register"
            );
          }}
        >
          Create Account
        </button>
      </div>

      <form
        className="auth-form"
        onSubmit={(event) => {
          void handleSubmit(event);
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

      <p className="auth-privacy-note">
        Your session is stored in a
        secure, HTTP-only cookie.
      </p>
    </dialog>
  );
}
