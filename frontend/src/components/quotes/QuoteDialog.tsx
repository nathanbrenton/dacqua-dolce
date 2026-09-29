import {
  type FormEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  submitQuoteRequest,
  type RecommendationContext,
} from "../../api/quotes";
import {
  isCompleteUsPhone,
} from "../../utils/phone";
import {
  UsPhoneInput,
} from "../forms/UsPhoneInput";

export type QuoteInquiryContext =
  | "general"
  | "recommendation"
  | "product";

type QuoteDialogProps = {
  open: boolean;
  productId: string | null;
  productName: string | null;
  inquiryContext: QuoteInquiryContext;
  initialEmail: string | null;
  recommendationContext: RecommendationContext | null;
  onClose: () => void;
};

export function QuoteDialog({
  open,
  productId,
  productName,
  inquiryContext,
  initialEmail,
  recommendationContext,
  onClose,
}: QuoteDialogProps) {
  const dialogRef =
    useRef<HTMLDialogElement>(null);

  const backdropPointerStartedOutsideRef =
    useRef(false);

  const [name, setName] =
    useState("");
  const [email, setEmail] =
    useState(initialEmail ?? "");
  const [phone, setPhone] =
    useState("");
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
      setName("");
      setEmail(initialEmail ?? "");
      setPhone("");
      setMessage("");
      setError(null);
      setSuccessId(null);
    }
  }, [open, initialEmail, inquiryContext, productId]);

  const isProductInquiry =
    inquiryContext === "product"
    && productName !== null;

  const dialogKicker = isProductInquiry
    ? "Request a Quote"
    : inquiryContext === "recommendation"
      ? "System Guidance"
      : "Talk to an Expert";

  const dialogTitle = isProductInquiry
    ? productName
    : inquiryContext === "recommendation"
      ? "Help me choose a system."
      : "Further improve your water";

  const messageHelper = isProductInquiry
    ? "Water concerns, water-use patterns, source water if known, and installation constraints can help us prepare a more useful quote."
    : inquiryContext === "recommendation"
      ? "Water priorities, source water if known, water-use patterns, and installation context can help us narrow the options."
      : "Water priorities, water-use patterns, source water if known, and installation context can help us find a useful starting point.";

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setError(null);

    if (
      phone.length > 0
      && !isCompleteUsPhone(phone)
    ) {
      setError(
        "Enter a complete "
        + "10-digit phone number.",
      );
      return;
    }

    setSubmitting(true);

    try {
      const response =
        await submitQuoteRequest({
          product_id: productId,
          name,
          email,
          phone: phone || null,
          message: message || null,
          recommendation_context: recommendationContext,
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
      onPointerDown={(event) => {
        const bounds =
          event.currentTarget
            .getBoundingClientRect();

        backdropPointerStartedOutsideRef.current =
          event.clientX < bounds.left
          || event.clientX > bounds.right
          || event.clientY < bounds.top
          || event.clientY > bounds.bottom;
      }}
      onPointerCancel={() => {
        backdropPointerStartedOutsideRef.current = false;
      }}
      onClick={(event) => {
        const startedOutside =
          backdropPointerStartedOutsideRef.current;

        /*
         * Reset before deciding what to do so a canceled or unusual
         * pointer sequence cannot affect a later interaction. Pointer
         * events cover mouse, pen, and touch input. A drag/selection
         * that starts inside the dialog therefore never becomes a
         * backdrop dismissal merely because it ends outside.
         */
        backdropPointerStartedOutsideRef.current = false;

        if (!startedOutside) {
          return;
        }

        const bounds =
          event.currentTarget
            .getBoundingClientRect();

        const clickedOutside =
          event.clientX < bounds.left
          || event.clientX > bounds.right
          || event.clientY < bounds.top
          || event.clientY > bounds.bottom;

        if (!clickedOutside) {
          return;
        }

        /*
         * showModal() keeps the underlying document inert. Consuming
         * the completed backdrop activation here ensures this one
         * mouse/touch/pen action only dismisses the modal and cannot
         * activate the page visually underneath it.
         */
        event.preventDefault();
        event.stopPropagation();
        onClose();
      }}
      onClose={onClose}
      onCancel={onClose}
    >
      <div className="quote-dialog-header">
        <div>
          <p className="auth-kicker">
            {dialogKicker}
          </p>

          <h2 id="quote-dialog-title">
            {dialogTitle}
          </h2>

          {isProductInquiry ? (
            <p className="quote-dialog-context">
              Your request will stay associated with this system.
            </p>
          ) : inquiryContext === "recommendation" ? (
            <p className="quote-dialog-context">
              No system is selected yet. We’ll start with your water priorities and installation context.
            </p>
          ) : null}
        </div>

        <button
          className="auth-close"
          type="button"
          aria-label={isProductInquiry ? "Close quote request" : "Close inquiry"}
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

            <UsPhoneInput
              inputMode="tel"
              autoComplete="tel"
              maxLength={14}
              pattern={
                "[(][0-9]{3}[)] "
                + "[0-9]{3}-"
                + "[0-9]{4}"
              }
              title={
                "Enter a 10-digit "
                + "US phone number."
              }
              placeholder={
                "(949) 555-1234"
              }
              value={phone}
              onValueChange={setPhone}
            />

            <small className="field-helper">
              Type the 10 digits;
              formatting is added
              automatically.
            </small>
          </label>

          <label>
            <span>
              Your water and installation{" "}
              <small>(optional)</small>
            </span>

            <textarea
              rows={5}
              aria-describedby="quote-message-helper"
              maxLength={4000}
              value={message}
              onChange={(event) => {
                setMessage(
                  event.target.value,
                );
              }}
            />

            <small
              id="quote-message-helper"
              className="field-helper"
            >
              {messageHelper}
            </small>
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
              : isProductInquiry
                ? "Send Quote Request"
                : "Send inquiry"}
          </button>
        </form>
      )}
    </dialog>
  );
}
