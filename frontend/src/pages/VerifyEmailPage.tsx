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
  | "verifying"
  | "verified"
  | "error";

export function VerifyEmailPage({
  token,
  onNavigate,
  onVerified,
}: VerifyEmailPageProps) {
  const [state, setState] =
    useState<VerificationState>(
      "verifying",
    );

  const [message, setMessage] =
    useState(
      "Verifying your email address…",
    );

  useEffect(() => {
    let active = true;

    void completeEmailVerification(
      token,
    )
      .then(async (result) => {
        if (!active) {
          return;
        }

        setState("verified");
        setMessage(result);

        await onVerified();
      })
      .catch(async (caught) => {
        if (!active) {
          return;
        }

        try {
          const account =
            await getCurrentAccount();

          if (
            active
            && account?.email_verified
          ) {
            setState("verified");
            setMessage(
              "This email address is already verified.",
            );
            return;
          }
        } catch {
          // Fall through to the token error.
        }

        if (!active) {
          return;
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
      });

    return () => {
      active = false;
    };
  }, [
    token,
    onVerified,
  ]);

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
          {state === "verifying"
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

        {state !== "verifying" ? (
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
