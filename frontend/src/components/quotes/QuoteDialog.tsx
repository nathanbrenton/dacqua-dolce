import {
  type FormEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import { submitQuoteRequest } from "../../api/quotes";

type QuoteDialogProps = {
  open: boolean;
  productId: string | null;
  productName: string | null;
  initialEmail: string | null;
  onClose: () => void;
};

export function QuoteDialog({
  open,
  productId,
  productName,
  initialEmail,
  onClose,
}: QuoteDialogProps) {
  const dialogRef =
    useRef<HTMLDialogElement>(null);

  const [name, setName] = useState("");
  const [email, setEmail] = useState(
    initialEmail ?? "",
  );
  const [phone, setPhone] = useState("");
  const [message, setMessage] =
    useState("");
  const [error, setError] =
    useState<string | null>(null);
  const [successId, setSuccessId] =
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
      setEmail(initialEmail ?? "");
      setError(null);
      setSuccessId(null);
    }
  }, [open, initialEmail]);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const response =
        await submitQuoteRequest({
          product_id: productId,
          name,
          email,
          phone: phone || null,
          message: message || null,
        });

      setSuccessId(response.id);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Quote request failed.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className="quote-dialog"
      aria-labelledby="quote-dialog-title"
      onClose={onClose}
      onCancel={onClose}
    >
      <div className="quote-dialog-header">
        <div>
          <p className="auth-kicker">
            Request a Quote
          </p>

          <h2 id="quote-dialog-title">
            {productName
              ?? "Tell us what you need."}
          </h2>
        </div>

        <button
          className="auth-close"
          type="button"
          aria-label="Close quote request"
          onClick={onClose}
        >
          ×
        </button>
      </div>

      {successId !== null ? (
        <div className="quote-success">
          <strong>
            Request received.
          </strong>

          <p>
            Your reference is{" "}
            <code>{successId}</code>.
          </p>

          <button
            type="button"
            className="auth-submit"
            onClick={onClose}
          >
            Close
          </button>
        </div>
      ) : (
        <form
          className="auth-form"
          onSubmit={(event) => {
            void handleSubmit(event);
          }}
        >
          <label>
            <span>Name</span>

            <input
              type="text"
              autoComplete="name"
              required
              maxLength={160}
              value={name}
              onChange={(event) => {
                setName(
                  event.target.value,
                );
              }}
            />
          </label>

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

          <label>
            <span>
              Phone{" "}
              <small>(optional)</small>
            </span>

            <input
              type="tel"
              autoComplete="tel"
              maxLength={50}
              value={phone}
              onChange={(event) => {
                setPhone(
                  event.target.value,
                );
              }}
            />
          </label>

          <label>
            <span>
              Message{" "}
              <small>(optional)</small>
            </span>

            <textarea
              rows={5}
              maxLength={4000}
              value={message}
              onChange={(event) => {
                setMessage(
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
            className="auth-submit"
            disabled={submitting}
          >
            {submitting
              ? "Sending..."
              : "Send Quote Request"}
          </button>
        </form>
      )}
    </dialog>
  );
}
