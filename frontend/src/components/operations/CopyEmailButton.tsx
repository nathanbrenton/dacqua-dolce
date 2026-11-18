import { useState } from "react";

/** An email address with a "Copy email" button next to it. */
export function CopyEmailButton({ email }: { email: string }) {
  const [copied, setCopied] = useState(false);

  async function copyEmail(): Promise<void> {
    try {
      await navigator.clipboard.writeText(email);
      setCopied(true);
      window.setTimeout(() => {
        setCopied(false);
      }, 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <span className="operations-email-action">
      <span>{email}</span>
      <button
        type="button"
        className="operations-copy-email"
        onClick={() => {
          void copyEmail();
        }}
      >
        {copied ? "Copied" : "Copy email"}
      </button>
    </span>
  );
}
