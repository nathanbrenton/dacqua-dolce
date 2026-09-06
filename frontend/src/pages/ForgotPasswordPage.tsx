import {
  type FormEvent,
  useState,
} from "react";

import {
  requestPasswordReset,
} from "../api/authentication";

type ForgotPasswordPageProps = {
  onNavigate: (path: string) => void;
};

export function ForgotPasswordPage({
  onNavigate,
}: ForgotPasswordPageProps) {
  const [email, setEmail] =
    useState("");

  const [message, setMessage] =
    useState<string | null>(null);

  const [error, setError] =
    useState<string | null>(null);

  const [submitting, setSubmitting] =
    useState(false);

  async function submit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setMessage(null);
    setError(null);
    setSubmitting(true);

    try {
      setMessage(
        await requestPasswordReset(
          email,
        ),
      );
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : (
              "Unable to submit the "
              + "password reset request."
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
          onNavigate("/");
        }}
      >
        ← Home
      </button>

      <section className="recovery-panel">
        <p className="eyebrow">
          Account Recovery
        </p>

        <h1>Reset your password.</h1>

        <p className="recovery-copy">
          Enter the email address for
          your account. For privacy,
          the response is the same
          whether or not an account
          exists.
        </p>

        <form
          className="account-form"
          onSubmit={(event) => {
            void submit(event);
          }}
        >
          <label>
            <span>Email address</span>

            <input
              type="email"
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

          {message !== null ? (
            <p
              className="recovery-success"
              role="status"
            >
              {message}
            </p>
          ) : null}

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
            disabled={submitting}
          >
            {submitting
              ? "Sending..."
              : "Send Reset Link"}
          </button>
        </form>
      </section>
    </main>
  );
}
