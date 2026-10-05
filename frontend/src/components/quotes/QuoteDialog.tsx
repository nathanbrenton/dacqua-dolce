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
  const [servicePostalCode, setServicePostalCode] =
    useState("");
  const [sourceWater, setSourceWater] =
    useState<SourceWater>("unsure");
  const [bathrooms, setBathrooms] =
    useState<BathroomCount>("unsure");
  const [occupants, setOccupants] =
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
      setServicePostalCode(
        recommendationContext?.service_postal_code ?? "",
      );
      setSourceWater(
        recommendationContext?.source_water ?? "unsure",
      );
      setBathrooms(
        recommendationContext?.bathrooms ?? "unsure",
      );
      setOccupants(
        recommendationContext?.occupants?.toString() ?? "",
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
      const qualificationContext = {
        ...(recommendationContext ?? emptyRecommendationContext()),
        source_water: sourceWater,
        service_postal_code:
          servicePostalCode.trim() || null,
        bathrooms,
        occupants:
          occupants === ""
            ? null
            : Number.parseInt(occupants, 10),
      } satisfies RecommendationContext;

      const response =
        await submitQuoteRequest({
          product_id: productId,
          name,
          email,
          phone: phone || null,
          message: message || null,
          recommendation_context: qualificationContext,
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
          aria-label="Close inquiry"
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

          <aside className="quote-purchase-boundary">
            <strong>Equipment-only launch</strong>
            <p>
              Installation is arranged separately from D&apos;Acqua Dolce&apos;s
              equipment sale. We ask about installation constraints only to help
              confirm product fit; this request does not include installation
              services.
            </p>
          </aside>

          <fieldset className="quote-qualification">
            <legend>Property basics</legend>

            <p className="field-helper">
              Requests that require assisted sales are reviewed by a D'Acqua
              Dolce employee before purchase. These basics help make that
              conversation useful.
            </p>

            <label>
              <span>Service ZIP code</span>
              <input
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
              <span>Household size <small>(optional)</small></span>
              <input
                type="number"
                min="1"
                inputMode="numeric"
                value={occupants}
                onChange={(event) => {
                  setOccupants(event.target.value);
                }}
              />
            </label>

            {sourceWater === "well" ? (
              <p className="field-helper">
                Well-water recommendations require employee review and
                third-party laboratory water-quality results before a final
                system recommendation.
              </p>
            ) : null}
          </fieldset>

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
