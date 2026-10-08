import { type FormEvent, useEffect, useState } from "react";

import type { AuthenticationStatus } from "../../api/authentication";
import {
  submitSupportRequest,
  type SupportRequestKind,
} from "../../api/support";
import { UsPhoneInput } from "../forms/UsPhoneInput";
import { TurnstileChallenge, turnstileConfigured } from "../forms/TurnstileChallenge";

type SupportRequestFormProps = {
  account: AuthenticationStatus | null;
  productId?: string | null;
  productName?: string | null;
  defaultKind?: SupportRequestKind;
};

export function SupportRequestForm({
  account,
  productId = null,
  productName = null,
  defaultKind = "general_support",
}: SupportRequestFormProps) {
  const [kind, setKind] = useState<SupportRequestKind>(defaultKind);
  const [name, setName] = useState("");
  const [email, setEmail] = useState(account?.email ?? "");
  const [phone, setPhone] = useState("");
  const [message, setMessage] = useState("");
  const [website, setWebsite] = useState("");
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [turnstileResetKey, setTurnstileResetKey] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    setEmail(account?.email ?? "");
  }, [account]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (turnstileConfigured && !turnstileToken) {
      setError("Complete the verification challenge.");
      return;
    }
    setBusy(true);
    setError(null);
    setNotice(null);

    try {
      const result = await submitSupportRequest({
        kind,
        name,
        email,
        phone: phone || null,
        product_id: productId,
        message,
        website: website || null,
      }, turnstileToken ?? undefined);
      setNotice(`${result.message} Reference: ${result.id}`);
      setMessage("");
      setWebsite("");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Your support request could not be sent.",
      );
    } finally {
      setBusy(false);
      setTurnstileToken(null);
      setTurnstileResetKey((value) => value + 1);
    }
  }

  return (
    <form className="support-request-form" onSubmit={(event) => void submit(event)}>
      {productName !== null ? (
        <p className="support-request-product">
          System: <strong>{productName}</strong>
        </p>
      ) : null}

      <div className="support-request-honeypot" aria-hidden="true">
        <label>
          <span>Website</span>
          <input
            type="text"
            value={website}
            tabIndex={-1}
            autoComplete="off"
            onChange={(event) => setWebsite(event.target.value)}
          />
        </label>
      </div>

      <label>
        <span>Support type</span>
        <select
          value={kind}
          onChange={(event) => setKind(event.target.value as SupportRequestKind)}
        >
          <option value="warranty">Warranty support</option>
          <option value="product_support">Product support</option>
          <option value="general_support">General support</option>
        </select>
      </label>

      <label>
        <span>Name</span>
        <input
          value={name}
          maxLength={160}
          required
          autoComplete="name"
          onChange={(event) => setName(event.target.value)}
        />
      </label>

      <label>
        <span>Email</span>
        <input
          type="email"
          value={email}
          maxLength={320}
          required
          autoComplete="email"
          readOnly={account?.authenticated === true}
          onChange={(event) => setEmail(event.target.value)}
        />
      </label>

      <label>
        <span>Phone (optional)</span>
        <UsPhoneInput
          inputMode="tel"
          autoComplete="tel"
          maxLength={14}
          pattern={"[(][0-9]{3}[)] [0-9]{3}-[0-9]{4}"}
          title="Enter a 10-digit US phone number."
          placeholder="(949) 555-1234"
          value={phone}
          onValueChange={setPhone}
        />
      </label>

      <label>
        <span>How can we help?</span>
        <textarea
          value={message}
          maxLength={4000}
          required
          rows={6}
          onChange={(event) => setMessage(event.target.value)}
        />
      </label>

      <TurnstileChallenge action="support" onToken={setTurnstileToken} resetKey={turnstileResetKey} />

      {error !== null ? <p className="support-request-error" role="alert">{error}</p> : null}
      {notice !== null ? <p className="support-request-notice" role="status">{notice}</p> : null}

      <button type="submit" className="primary-button" disabled={busy}>
        {busy ? "Sending…" : "Send support request"}
      </button>
    </form>
  );
}
