import {
  type FormEvent,
  useState,
} from "react";

import {
  completePasswordReset,
} from "../api/authentication";

type ResetPasswordPageProps = {
  token: string;
  onNavigate: (path: string) => void;
  onResetComplete: () => void;
};

export function ResetPasswordPage({
  token,
  onNavigate,
  onResetComplete,
}: ResetPasswordPageProps) {
  const [password, setPassword] =
    useState("");

  const [
    passwordConfirmation,
    setPasswordConfirmation,
  ] = useState("");

  const [error, setError] =
    useState<string | null>(null);

  const [submitting, setSubmitting] =
    useState(false);

  async function submit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setError(null);

    if (
      password
      !== passwordConfirmation
    ) {
      setError(
        "Passwords do not match."
      );
      return;
    }

    setSubmitting(true);

    try {
      await completePasswordReset(
        token,
        password,
      );

      onNavigate("/");
      onResetComplete();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : (
              "Unable to reset the "
              + "password."
            ),
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="recovery-shell">
      <button
        type="button"
        className="text-button"
        onClick={() => {
          onNavigate(
            "/forgot-password",
          );
        }}
      >
        ← Request another link
      </button>

      <section className="recovery-panel">
        <p className="eyebrow">
          Account Recovery
        </p>

        <h1>Choose a new password.</h1>

        <p className="recovery-copy">
          Reset links are single-use
          and expire after 30 minutes.
          A successful reset signs out
          every existing session.
        </p>

        <form
          className="account-form"
          onSubmit={(event) => {
            void submit(event);
          }}
        >
          <label>
            <span>New password</span>

            <input
              type="password"
              autoComplete="new-password"
              required
              minLength={12}
              maxLength={256}
              value={password}
              onChange={(event) => {
                setPassword(
                  event.target.value,
                );
              }}
            />
          </label>

          <label>
            <span>
              Confirm new password
            </span>

            <input
              type="password"
              autoComplete="new-password"
              required
              minLength={12}
              maxLength={256}
              value={
                passwordConfirmation
              }
              onChange={(event) => {
                setPasswordConfirmation(
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
            type="submit"
            className="account-action"
            disabled={
              submitting
              || token.length === 0
            }
          >
            {submitting
              ? "Updating..."
              : "Update Password"}
          </button>
        </form>
      </section>
    </main>
  );
}
