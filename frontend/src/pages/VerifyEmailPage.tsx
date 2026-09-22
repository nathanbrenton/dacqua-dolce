import {
  useEffect,
  useState,
} from "react";

import {
  completeEmailVerification,
  getCurrentAccount,
} from "../api/authentication";

type VerifyEmailPageProps = {
  token: string;
  onNavigate: (path: string) => void;
  onVerified: () => Promise<void>;
};

type VerificationState =
  | "ready"
  | "verifying"
  | "verified"
  | "error";

const READY_MESSAGE = (
  "Select Verify email address to complete verification."
);

export function VerifyEmailPage({
  token,
  onNavigate,
  onVerified,
}: VerifyEmailPageProps) {
  const [state, setState] =
    useState<VerificationState>(
      "ready",
    );

  const [message, setMessage] =
    useState(READY_MESSAGE);

  useEffect(() => {
    setState("ready");
    setMessage(READY_MESSAGE);
  }, [token]);

  async function verifyEmail() {
    setState("verifying");
    setMessage(
      "Verifying your email address…",
    );

    try {
      const result =
        await completeEmailVerification(
          token,
        );

      setState("verified");
      setMessage(result);

      await onVerified();
    } catch (caught) {
      try {
        const account =
          await getCurrentAccount();

        if (account?.email_verified) {
          setState("verified");
          setMessage(
            "This email address is already verified.",
          );
          return;
        }
      } catch {
        // Fall through to the token error.
      }

      setState("error");

      setMessage(
        caught instanceof Error
          ? caught.message
          : (
              "Email verification "
              + "could not be completed."
            ),
      );
    }
  }

  return (
    <main className="detail-shell">
      <button
        type="button"
        className="text-button"
        onClick={() => {
          onNavigate("/");
        }}
      >
        ← Home
      </button>

      <section className="email-verification-page">
        <p className="eyebrow">
          Account Security
        </p>

        <h1>
          {state === "ready"
            ? "Verify your email."
            : state === "verifying"
              ? "Verifying your email."
              : state === "verified"
                ? "Email verified."
                : "Verification link unavailable."}
        </h1>

        <p
          role={
            state === "error"
              ? "alert"
              : "status"
          }
        >
          {message}
        </p>

        {state === "ready" ? (
          <button
            type="button"
            className="detail-primary-action"
            onClick={() => {
              void verifyEmail();
            }}
          >
            Verify email address
          </button>
        ) : state !== "verifying" ? (
          <button
            type="button"
            className="detail-primary-action"
            onClick={() => {
              onNavigate(
                state === "verified"
                  ? "/account"
                  : "/",
              );
            }}
          >
            {state === "verified"
              ? "Continue to Account"
              : "Return Home"}
          </button>
        ) : null}
      </section>
    </main>
  );
}
