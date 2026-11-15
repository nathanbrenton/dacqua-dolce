import { type FormEvent, useEffect, useState } from "react";

import type { AuthenticationStatus } from "../../api/authentication";
import {
  submitSupportRequest,
  type SupportRequestKind,
} from "../../api/support";
import {
  type ContactMethod,
  DEFAULT_CONTACT_METHOD,
  PHONE_REQUIRED_MESSAGE,
  contactMethodNeedsPhone,
} from "../../utils/contactMethod";
import { isCompleteUsPhone } from "../../utils/phone";
import { loadAccountContactDefaults } from "../forms/accountContactDefaults";
import { ContactMethodSelect } from "../forms/ContactMethodSelect";
import { UsPhoneInput } from "../forms/UsPhoneInput";
import { useToast } from "../toast/ToastProvider";
import { TurnstileChallenge, turnstileConfigured } from "../forms/TurnstileChallenge";

type SupportRequestFormProps = {
  account: AuthenticationStatus | null;
  productId?: string | null;
  productName?: string | null;
  defaultKind?: SupportRequestKind;
  onNavigate?: (path: string) => void;
};

export function SupportRequestForm({
  account,
  productId = null,
  productName = null,
  defaultKind = "general_support",
  onNavigate,
}: SupportRequestFormProps) {
  const [kind, setKind] = useState<SupportRequestKind>(defaultKind);
  const [name, setName] = useState("");
  const [email, setEmail] = useState(account?.email ?? "");
  const [phone, setPhone] = useState("");
  const [contactMethod, setContactMethod] =
    useState<ContactMethod>(DEFAULT_CONTACT_METHOD);
  const [message, setMessage] = useState("");
  const [website, setWebsite] = useState("");
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [turnstileResetKey, setTurnstileResetKey] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [receiptId, setReceiptId] = useState<string | null>(null);
  const toast = useToast();

  useEffect(() => {
    setEmail(account?.email ?? "");
  }, [account]);

  // Signed-in customers start with their saved name, phone and preference.
  useEffect(() => {
    if (account?.authenticated !== true) {
      return;
    }
    let cancelled = false;
    void loadAccountContactDefaults().then((defaults) => {
      if (cancelled || defaults === null) {
        return;
      }
      setName((current) => current || defaults.name);
      setPhone((current) => current || defaults.phone);
      if (defaults.method !== null) {
        setContactMethod(defaults.method);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [account?.authenticated]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (contactMethodNeedsPhone(contactMethod) && phone.length === 0) {
      setError(PHONE_REQUIRED_MESSAGE);
      return;
    }
    if (phone.length > 0 && !isCompleteUsPhone(phone)) {
      setError("Enter a complete 10-digit phone number.");
      return;
    }
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
        preferred_contact_method: contactMethod,
        product_id: productId,
        message,
        website: website || null,
      }, turnstileToken ?? undefined);
      setNotice(result.message);
      setReceiptId(result.id);
      toast.success("Support request received");
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
        <span>
          Phone
          {contactMethodNeedsPhone(contactMethod) ? null : " (optional)"}
        </span>
        <UsPhoneInput
          required={contactMethodNeedsPhone(contactMethod)}
          inputMode="tel"
          autoComplete="tel"
          maxLength={14}
          pattern={"[(][0-9]{3}[)] [0-9]{3}-[0-9]{4}"}
          title="Enter a 10-digit US phone number."
          placeholder="(951) 555-0142"
          value={phone}
          onValueChange={setPhone}
        />
      </label>

      <ContactMethodSelect value={contactMethod} onChange={setContactMethod} />

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
      {notice !== null ? (
        <div className="support-request-confirmation" role="status">
          <h3>Support request received</h3>
          <p>{notice}</p>
          <p>Reference: <strong>{receiptId}</strong></p>
          <a
            className="primary-button support-request-home-link"
            href="/"
            onClick={(event) => {
              if (onNavigate) {
                event.preventDefault();
                onNavigate("/");
              }
            }}
          >
            Return to homepage
          </a>
        </div>
      ) : null}

      {notice === null ? <button type="submit" className="primary-button" disabled={busy}>
        {busy ? "Sending…" : "Send support request"}
      </button> : null}

    </form>
  );
}
