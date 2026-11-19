// One customer request in the Requests workspace's detail pane: workflow
// progress and next step, customer contact, recommendation, the request
// message, the email conversation, the formal quote composer and private notes.
//
// Parts in their own files: ../RequestWorkflowProgress.tsx (progress bar;
// rules in ../operationsNextSteps.ts), ../RequestConversation.tsx (thread and
// reply; GET/POST /api/operations/quotes/{id}/conversation),
// ../FormalQuoteComposer.tsx (quote drafting and presenting).
// Status and notes saves are handled by workspaces/RequestsWorkspace.tsx.

import type {
  OperationsFormalQuote,
  OperationsProduct,
  OperationsQuote,
  OperationsCommunicationThreadDetail,
} from "../../../api/operations";
import { contactMethodLabel } from "../../../utils/contactMethod";
import { formatUsPhoneInput } from "../../../utils/phone";
import { CopyEmailButton } from "../CopyEmailButton";
import { FormalQuoteComposer } from "../FormalQuoteComposer";
import { splitRequestMessage } from "../operationsMoney";
import type { SaveState } from "../operationsShared";
import { RequestConversation } from "../RequestConversation";
import { RequestWorkflowProgress } from "../RequestWorkflowProgress";
import {
  RECOMMENDATION_COMPONENT_LABELS,
  recommendationContextLabel,
  recommendationContextValue,
} from "./requestLabels";

type RequestDetailProps = {
  quote: OperationsQuote;
  products: OperationsProduct[];
  privileged: boolean;
  /** Shown in the detail pane (unselected requests stay mounted but hidden). */
  selected: boolean;
  /** Selected and the Requests workspace is open (loads the conversation). */
  active: boolean;
  noteDraft: string;
  noteSaveState: SaveState;
  onNoteDraftChange: (value: string) => void;
  onSaveNotes: () => void;
  onSaveStatus: (status: string) => void;
  onFormalQuoteChange: (requestId: string, formalQuote: OperationsFormalQuote) => void;
  onReplied: (thread: OperationsCommunicationThreadDetail) => void;
  onOpenThreadInInbox: (threadId: string) => void;
};

export function RequestDetail({
  quote,
  products,
  privileged,
  selected,
  active,
  noteDraft,
  noteSaveState,
  onNoteDraftChange,
  onSaveNotes,
  onSaveStatus,
  onFormalQuoteChange,
  onReplied,
  onOpenThreadInInbox,
}: RequestDetailProps) {
  return (
    <article
      id={`operations-request-${quote.id}`}
      hidden={!selected}
      className="operations-quote"
      data-quote-status={quote.status}
      data-human-review={
        quote.recommendation_decision?.human_review === true
          ? "true"
          : "false"
      }
      data-lab-testing={
        quote.recommendation_decision?.requires_third_party_lab === true
          ? "true"
          : "false"
      }
    >
      <div className="operations-request-workspace">
        <header className="operations-request-header">
          <div>
            <p className="product-meta">
              {quote.product_name ?? "General consultation"}
            </p>
            <h3>{quote.name}</h3>
          </div>
          <span className="operations-request-created">
            Received {new Date(quote.created_at).toLocaleString()}
          </span>
        </header>

        <RequestWorkflowProgress
          quote={quote}
          onSetStatus={(status) => {
            onSaveStatus(status);
          }}
          onOpenQuote={() => {
            document
              .getElementById(`operations-request-${quote.id}`)
              ?.querySelector(".operations-formal-quote")
              ?.scrollIntoView({ behavior: "smooth", block: "start" });
          }}
        />

        <section className="operations-request-region">
          <p className="operations-request-region-label">Customer</p>
          <div className="operations-request-contact">
            <CopyEmailButton email={quote.email} />
            {quote.phone !== null ? (
              <a href={`tel:${quote.phone}`}>
                {formatUsPhoneInput(quote.phone)}
              </a>
            ) : null}
            {quote.phone !== null
            && quote.preferred_contact_method === "text" ? (
              <a href={`sms:${quote.phone}`}>Text</a>
            ) : null}
            {contactMethodLabel(quote.preferred_contact_method) !== null ? (
              <span
                className="operations-contact-preference"
                data-method={quote.preferred_contact_method}
              >
                Prefers {contactMethodLabel(quote.preferred_contact_method)?.toLowerCase()}
              </span>
            ) : null}
          </div>
        </section>

        {quote.recommendation_decision !== null ? (
          <section
            className={
              "operations-request-region "
              + "operations-recommendation-result"
            }
          >
            <div className="operations-request-region-heading">
              <p className="operations-request-region-label">
                Recommendation result
              </p>
              <span>
                Policy v{quote.recommendation_policy_version ?? "legacy"}
              </span>
            </div>

            <div className="operations-recommendation-flags">
              <span>Guided recommendation</span>
              {quote.recommendation_decision.human_review ? (
                <span>Staff review required</span>
              ) : (
                <span>Historical automatic starting path</span>
              )}
              {quote.recommendation_decision.requires_third_party_lab ? (
                <span className="is-important">
                  Third-party lab required
                </span>
              ) : null}
            </div>

            <h4>{quote.recommendation_decision.title}</h4>
            <p>{quote.recommendation_decision.description}</p>

            {quote.recommendation_decision.sizing ? (
              <div className="operations-recommendation-sizing">
                <strong>Capacity sizing</strong>
                <span>
                  {quote.recommendation_decision.sizing.status === "inputs_complete"
                    ? "Inputs complete; verified capacity rules are still pending."
                    : `Needs more information: ${quote.recommendation_decision.sizing.missing_inputs
                      .map((input) => recommendationContextLabel(input))
                      .join(", ")}.`}
                </span>
              </div>
            ) : null}

            {quote.recommendation_decision.components.length > 0 ? (
              <div className="operations-recommendation-components">
                {quote.recommendation_decision.components.map(
                  (component) => (
                    <span key={component}>
                      {RECOMMENDATION_COMPONENT_LABELS[component] ?? component}
                    </span>
                  ),
                )}
              </div>
            ) : null}
          </section>
        ) : quote.recommendation_context !== null ? (
          <section
            className={
              "operations-request-region "
              + "operations-recommendation-legacy"
            }
          >
            <p className="operations-request-region-label">
              Guided recommendation
            </p>
            <p>
              This request predates decision snapshots. Review the
              submitted context manually.
            </p>
          </section>
        ) : null}

        {quote.recommendation_context !== null ? (
          <section className="operations-request-region">
            <p className="operations-request-region-label">
              Recommendation context
            </p>
            <dl className="operations-recommendation-context">
              {Object.entries(quote.recommendation_context).map(
                ([key, value]) => (
                  <div key={key}>
                    <dt>{recommendationContextLabel(key)}</dt>
                    <dd>{recommendationContextValue(key, value)}</dd>
                  </div>
                ),
              )}
            </dl>
          </section>
        ) : null}

        <section className="operations-request-region">
          <p className="operations-request-region-label">Request</p>
          {(() => {
            const { configuration, customerMessage } =
              splitRequestMessage(quote.message);
            return (
              <>
                {configuration !== null ? (
                  <details className="operations-request-configuration">
                    <summary>
                      Requested configuration
                      <span>
                        {configuration.split("\n")[1]?.replace(
                          /^Catalog reference SKU:\s*/,
                          "",
                        ) ?? ""}
                      </span>
                    </summary>
                    <p className="operations-customer-message">
                      {configuration}
                    </p>
                  </details>
                ) : null}
                {customerMessage !== null ? (
                  <p className="operations-customer-message">
                    {customerMessage}
                  </p>
                ) : (
                  <p className="operations-request-empty">
                    No customer message was provided.
                  </p>
                )}
              </>
            );
          })()}
        </section>

        <RequestConversation
          quote={quote}
          active={active}
          onReplied={(reply) => {
            onReplied(reply.thread);
            // Emailing a new request's customer is contacting them.
            if (
              quote.status === "new"
              && reply.delivery_status !== "failed"
            ) {
              onSaveStatus("contacted");
            }
          }}
          onOpenInInbox={onOpenThreadInInbox}
        />

        <FormalQuoteComposer
          quote={quote}
          products={products}
          canOverrideCatalogPricing={privileged}
          onChanged={onFormalQuoteChange}
        />

        <section
          className={
            "operations-request-region "
            + "operations-request-private"
          }
        >
          <div className="operations-request-region-heading">
            <p className="operations-request-region-label">
              Internal follow-up
            </p>
            <span>Private — never shown to the customer.</span>
          </div>

          <label className="operations-field">
            <span className="sr-only">Internal notes</span>
            <textarea
              rows={3}
              maxLength={8000}
              placeholder="Add private follow-up notes"
              value={noteDraft}
              onChange={(event) => {
                onNoteDraftChange(event.target.value);
              }}
            />
          </label>

          <button
            type="button"
            className={
              "operations-action secondary "
              + (
                noteSaveState === "saved"
                  ? "is-saved"
                  : ""
              )
            }
            disabled={
              noteSaveState === "saving"
            }
            onClick={() => {
              onSaveNotes();
            }}
          >
            {noteSaveState === "saving"
              ? "Saving…"
              : noteSaveState === "saved"
                ? "Saved ✓"
                : "Save Internal Notes"}
          </button>
        </section>
      </div>
    </article>
  );
}
