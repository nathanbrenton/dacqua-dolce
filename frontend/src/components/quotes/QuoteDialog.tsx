import {
  type FormEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  type ContactMethod,
  DEFAULT_CONTACT_METHOD,
  PHONE_REQUIRED_MESSAGE,
  contactMethodFollowUp,
  contactMethodNeedsPhone,
} from "../../utils/contactMethod";
import { loadAccountContactDefaults } from "../forms/accountContactDefaults";
import { ContactMethodSelect } from "../forms/ContactMethodSelect";
import {
  HOME_SIZE_OPTIONS,
  submitQuoteRequest,
  type HomeSize,
  type RecommendationContext,
  type ProductQuoteConfiguration,
} from "../../api/quotes";
import {
  isCompleteUsPhone,
} from "../../utils/phone";
import { shortClackFittingLabel, type ClackInstallationFitting } from "../catalog/clackInstallationFittings";
import { TurnstileChallenge, turnstileConfigured } from "../forms/TurnstileChallenge";
import {
  UsPhoneInput,
} from "../forms/UsPhoneInput";
import { exactEntryProps, proseEntryProps } from "../forms/textEntry";

export type QuoteInquiryContext =
  | "general"
  | "recommendation"
  | "product";

type SourceWater = RecommendationContext["source_water"];
type BathroomCount = RecommendationContext["bathrooms"];

function emptyRecommendationContext(): RecommendationContext {
  return {
    source_water: "unsure",
    service_postal_code: null,
    hard_water_signs: "unsure",
    water_hardness: null,
    bathrooms: "unsure",
    occupants: null,
    water_service_pipe_size: null,
    water_quality_report_read: "unsure",
    chlorine_chloramine_signs: "unsure",
    chlorine_chloramine_details: null,
    iron_manganese_concerns: "unsure",
    iron_manganese_details: null,
    ph: null,
    existing_equipment: null,
    drain_available: "unsure",
    electrical_available: "unsure",
    irrigation_hose_bib: "unsure",
    pool_autofill: "unsure",
    drinking_water_ro: "unsure",
    water_test_results: "unsure",
    water_filtration_network: "unsure",
    water_filtration_network_details: null,
    treatment_preference: "unsure",
  };
}

type QuoteDialogProps = {
  open: boolean;
  productId: string | null;
  productName: string | null;
  inquiryContext: QuoteInquiryContext;
  initialEmail: string | null;
  recommendationContext: RecommendationContext | null;
  installationFitting?: ClackInstallationFitting | null;
  configurationNote?: string | null;
  productConfiguration?: ProductQuoteConfiguration | null;
  onClose: () => void;
};

export function QuoteDialog({
  open,
  productId,
  productName,
  inquiryContext,
  initialEmail,
  recommendationContext,
  installationFitting = null,
  configurationNote = null,
  productConfiguration = null,
  onClose,
}: QuoteDialogProps) {
  const dialogRef =
    useRef<HTMLDialogElement>(null);

  const successRef =
    useRef<HTMLDivElement>(null);

  const backdropPointerStartedOutsideRef =
    useRef(false);

  const [name, setName] =
    useState("");
  const [email, setEmail] =
    useState(initialEmail ?? "");
  const [phone, setPhone] =
    useState("");
  const [contactMethod, setContactMethod] =
    useState<ContactMethod>(DEFAULT_CONTACT_METHOD);
  const [servicePostalCode, setServicePostalCode] =
    useState("");
  const [sourceWater, setSourceWater] =
    useState<SourceWater>("unsure");
  const [bathrooms, setBathrooms] =
    useState<BathroomCount>("unsure");
  const [homeSize, setHomeSize] =
    useState<HomeSize>("unsure");
  const [message, setMessage] =
    useState("");
  const [error, setError] =
    useState<string | null>(null);
  const [successId, setSuccessId] =
    useState<string | null>(null);
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [turnstileResetKey, setTurnstileResetKey] = useState(0);
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
      setContactMethod(DEFAULT_CONTACT_METHOD);
      setServicePostalCode(
        recommendationContext?.service_postal_code ?? "",
      );
      setSourceWater(
        recommendationContext?.source_water ?? "unsure",
      );
      setBathrooms(
        recommendationContext?.bathrooms ?? "unsure",
      );
      setHomeSize(
        recommendationContext?.home_size ?? "unsure",
      );
      setMessage("");
      setError(null);
      setSuccessId(null);
    }
  }, [
    open,
    initialEmail,
    inquiryContext,
    productId,
    recommendationContext,
  ]);

  // Signed-in customers start with their saved name, phone and preference.
  useEffect(() => {
    if (!open || initialEmail === null) {
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
  }, [open, initialEmail]);

  useEffect(() => {
    if (successId === null) {
      return;
    }

    const frame = window.requestAnimationFrame(() => {
      successRef.current?.focus({ preventScroll: true });
    });

    return () => {
      window.cancelAnimationFrame(frame);
    };
  }, [successId]);

  const isProductInquiry =
    inquiryContext === "product"
    && productName !== null;

  const dialogKicker = isProductInquiry
    ? "Product Inquiry"
    : inquiryContext === "recommendation"
      ? "System Guidance"
      : "Talk to an Expert";

  const dialogTitle = isProductInquiry
    ? productName
    : inquiryContext === "recommendation"
      ? "Help me choose a system."
      : "How can we help with your water?";

  const messageHelper = isProductInquiry
    ? "Anything about your water, how you use it and where the system will go helps us prepare a more useful quote."
    : inquiryContext === "recommendation"
      ? "Tell us what matters most about your water, how you use it and where the system will go, and we'll narrow the options."
      : "Tell us what matters most about your water, how you use it and where a system would go, and we'll find a starting point.";

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setError(null);

    if (contactMethodNeedsPhone(contactMethod) && phone.length === 0) {
      setError(PHONE_REQUIRED_MESSAGE);
      return;
    }

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

    if (turnstileConfigured && !turnstileToken) {
      setError("Complete the verification challenge.");
      return;
    }
    // The public quote API currently supports a free-text message, not
    // structured or priced fitting line items. Include the selected fitting
    // explicitly so operations can review and confirm it before quoting.
    const fittingNote = installationFitting === null
      ? ""
      : `Requested Clack fitting: ${installationFitting.size} — ${installationFitting.label}; Clack order no. ${installationFitting.orderNo}. Compatibility, availability and final price to be confirmed.`;
    // PT54-A: the server renders a validated configuration summary. Existing
    // legacy callers still send their fitting notes as before.
    const combinedMessage = [
      ...(productConfiguration === null ? [fittingNote, configurationNote] : []),
      message.trim(),
    ].filter(Boolean).join("\n\n");
    if (combinedMessage.length > 4000) {
      setError("Shorten your message to include the selected fitting details.");
      return;
    }
    setSubmitting(true);

    try {
      const qualificationContext = {
        ...(recommendationContext ?? emptyRecommendationContext()),
        source_water: sourceWater,
        service_postal_code:
          servicePostalCode.trim() || null,
        bathrooms,
        home_size: homeSize,
      } satisfies RecommendationContext;

      const response =
        await submitQuoteRequest({
          inquiry_context:
            inquiryContext === "product"
              ? "product_inquiry"
              : inquiryContext === "recommendation"
                ? "recommendation_inquiry"
                : "expert_inquiry",
          product_id: productId,
          name,
          email,
          phone: phone || null,
          preferred_contact_method: contactMethod,
          message: combinedMessage || null,
          recommendation_context: qualificationContext,
          configuration: productConfiguration,
        }, turnstileToken ?? undefined);

      setSuccessId(response.id);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Quote request failed.",
      );
    } finally {
      setSubmitting(false);
      setTurnstileToken(null);
      setTurnstileResetKey((value) => value + 1);
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

          {configurationNote !== null && isProductInquiry ? (
            <p className="product-ownership-guidance" style={{ whiteSpace: "pre-line" }}>
              {configurationNote}
            </p>
          ) : null}
          {installationFitting !== null && isProductInquiry ? (
            <p className="quote-dialog-context">
              Requested connection fitting: {installationFitting.size} — {shortClackFittingLabel(installationFitting)}.
              We&apos;ll confirm its cost and availability with your quote.
            </p>
          ) : null}
          {isProductInquiry ? (
            <p className="quote-dialog-context">
              We&apos;ll prepare your quote for this system.
            </p>
          ) : inquiryContext === "recommendation" ? (
            <p className="quote-dialog-context">
              No system selected yet. We’ll start from what matters to you and where a system would go.
            </p>
          ) : null}
        </div>

        <button
          className="auth-close"
          type="button"
          aria-label="Close inquiry"
          onClick={onClose}
        >
          ×
        </button>
      </div>

      {successId !== null ? (
        <div
          ref={successRef}
          className="quote-success"
          role="status"
          tabIndex={-1}
        >
          <strong>
            Request received.
          </strong>

          <p>
            Thank you. Our team will review it and{" "}
            {contactMethodFollowUp(contactMethod)}. Your reference is{" "}
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
              {...exactEntryProps}
              type="text"
              autoComplete="name"
              autoFocus
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
              {...exactEntryProps}
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
              {contactMethodNeedsPhone(contactMethod)
                ? null
                : <small>(optional)</small>}
            </span>

            <UsPhoneInput
              required={contactMethodNeedsPhone(contactMethod)}
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
                "(951) 555-0142"
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

          <ContactMethodSelect
            value={contactMethod}
            onChange={setContactMethod}
          />

          <aside className="quote-purchase-boundary">
            <strong>Equipment only</strong>
            <p>
              Installation is arranged separately and is not part of this
              request. We ask about your installation only to confirm the
              system will fit.
            </p>
          </aside>

          <fieldset className="quote-qualification">
            <legend>About your home</legend>

            <p className="field-helper">
              Our team reviews requests like this one before purchase. A few
              basics help us give you a useful answer.
            </p>

            <label>
              <span>Service ZIP code</span>
              <input
                {...exactEntryProps}
                type="text"
                inputMode="numeric"
                autoComplete="postal-code"
                required
                minLength={5}
                maxLength={20}
                value={servicePostalCode}
                onChange={(event) => {
                  setServicePostalCode(event.target.value);
                }}
              />
            </label>

            <label>
              <span>Source water</span>
              <select
                value={sourceWater}
                onChange={(event) => {
                  setSourceWater(
                    event.target.value as SourceWater,
                  );
                }}
              >
                <option value="unsure">Not sure</option>
                <option value="municipal">Municipal water</option>
                <option value="well">Private well</option>
              </select>
            </label>

            <label>
              <span>Number of bathrooms</span>
              <select
                value={bathrooms}
                onChange={(event) => {
                  setBathrooms(
                    event.target.value as BathroomCount,
                  );
                }}
              >
                <option value="unsure">Not sure</option>
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="4">4</option>
                <option value="5+">5 or more</option>
              </select>
            </label>

            <label>
              <span>Approximate household size</span>
              <select
                value={homeSize}
                onChange={(event) => {
                  setHomeSize(event.target.value as HomeSize);
                }}
              >
                {HOME_SIZE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            {sourceWater === "well" ? (
              <p className="field-helper">
                For well water, we need third-party laboratory results and a
                review by our team before we make a final recommendation.
              </p>
            ) : null}
          </fieldset>

          <label>
            <span>
              Your water and installation{" "}
              <small>(optional)</small>
            </span>

            <textarea
              {...proseEntryProps}
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

          <TurnstileChallenge action="quote" onToken={setTurnstileToken} resetKey={turnstileResetKey} />
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
