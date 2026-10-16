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
  canResend: boolean;
  onResend: () => Promise<string>;
  onRequestSignIn: () => void;
  onNavigate: (path: string) => void;
  onVerified: () => Promise<void>;
};

type VerificationState =
  | "ready"
  | "verifying"
  | "verified"
  | "error"
  | "resending"
  | "resent";

const READY_MESSAGE =
  "Select Verify email address to complete verification. You can do this even if you registered in another browser.";

export function VerifyEmailPage({
  token,
  canResend,
  onResend,
  onRequestSignIn,
  onNavigate,
  onVerified,
}: VerifyEmailPageProps) {
  const [state, setState] =
    useState<VerificationState>("ready");
  const [message, setMessage] =
    useState(READY_MESSAGE);

  useEffect(() => {
    setState("ready");
    setMessage(READY_MESSAGE);
  }, [token]);

  async function finishVerified(messageText: string) {
    setState("verified");
    setMessage(messageText);

    // Email verification does not require the same browser session as
    // registration. Failure to refresh this browser's login state must
    // not turn a successful verification into a misleading error.
    try {
      await onVerified();
    } catch {
      // Account access can be refreshed after the customer signs in.
    }
  }

  async function verifyEmail() {
    if (state !== "ready" && state !== "error") {
      return;
    }

    setState("verifying");
    setMessage("Verifying your email address…");

    let result: string;
    try {
      result = await completeEmailVerification(token);
    } catch (caught) {
      try {
        const account = await getCurrentAccount();
        if (account?.email_verified) {
          await finishVerified(
            "This email address is already verified.",
          );
          return;
        }
      } catch {
        // Preserve the original verification result below.
      }

      setState("error");
      setMessage(
        caught instanceof Error
          ? caught.message
          : "Email verification could not be completed.",
      );
      return;
    }

    await finishVerified(result);
  }

  async function resendEmail() {
    if (!canResend || state === "resending" || state === "verifying") {
      return;
    }

    setState("resending");
    setMessage("Requesting another verification email…");

    try {
      await onResend();
      setState("resent");
      setMessage(
        "Another verification email has been requested. Check your inbox and open the email to complete verification.",
      );
    } catch (caught) {
      setState("error");
      setMessage(
        caught instanceof Error
          ? caught.message
          : "We could not request another email. Please try again.",
      );
    }
  }

  const error = state === "error";

  return (
    <main id="main-content" tabIndex={-1} className="detail-shell">
      <button
        type="button"
        className="text-button"
        onClick={() => onNavigate("/")}
      >
        ← Home
      </button>

      <section className="email-verification-page">
        <p className="eyebrow">Account Security</p>

        <h1>
          {state === "verified"
            ? "Email verified."
            : state === "resent"
              ? "Check your email."
              : state === "resending"
                ? "Sending another email."
                : state === "verifying"
                  ? "Verifying your email."
                : error
                  ? "Verification link unavailable."
                  : "Verify your email."}
        </h1>

        <p role={error ? "alert" : "status"}>{message}</p>

        {state === "ready" ? (
          <button
            type="button"
            className="detail-primary-action"
            onClick={() => void verifyEmail()}
          >
            Verify email address
          </button>
        ) : null}

        {error ? (
          <>
            <p>
              The link may have been replaced by another email, used
              already, or expired. You don&apos;t need to copy the URL
              or return to the browser where you signed up.
            </p>
            {canResend ? (
              <button
                type="button"
                className="detail-primary-action"
                onClick={() => void resendEmail()}
              >
                Send another verification email
              </button>
            ) : (
              <>
                <p>
                  Sign in with your account email and password to
                  request another verification email if needed.
                </p>
                <button
                  type="button"
                  className="detail-primary-action"
                  onClick={onRequestSignIn}
                >
                  Sign in to request another link
                </button>
              </>
            )}
          </>
        ) : null}

        {state === "verified" ? (
          <>
            <p>
              You can continue to your account. If this browser
              isn&apos;t signed in, simply sign in with your email
              and password.
            </p>
            <button
              type="button"
              className="detail-primary-action"
              onClick={() => onNavigate("/account")}
            >
              Continue to Account
            </button>
          </>
        ) : null}

        {state === "resent" ? (
          <button
            type="button"
            className="text-button"
            onClick={() => onNavigate("/")}
          >
            Return Home
          </button>
        ) : null}

        {error ? (
          <button
            type="button"
            className="text-button"
            onClick={() => onNavigate("/")}
          >
            Return Home
          </button>
        ) : null}
      </section>
    </main>
  );
}
