// Requests workspace of Operations: status and recommendation-triage filters,
// the request queue on the left, and the selected request's detail pane
// (requests/RequestDetail.tsx) on the right. Every request in the current view
// stays mounted (unselected ones are hidden) so quote drafts survive switching;
// private-note drafts are kept here so they also survive filter changes.
//
// The request list, filters and selection are owned by OperationsPage because
// Overview shortcuts and Inbox "Open request" links set them.
//
// API: updateQuoteStatus, updateQuoteNotes in api/operations.ts
//   -> PATCH /api/operations/quotes/{id}, PUT /api/operations/quotes/{id}/notes
// Styles: .operations-request-* in styles.css

import {
  type Dispatch,
  type SetStateAction,
  useMemo,
  useState,
} from "react";

import {
  updateQuoteNotes,
  updateQuoteStatus,
  type OperationsCommunicationThreadDetail,
  type OperationsFormalQuote,
  type OperationsProduct,
  type OperationsQuote,
} from "../../../api/operations";
import { formatRequestAge } from "../formatRequestAge";
import type { OperationsNoticeProps, SaveState } from "../operationsShared";
import { RequestDetail } from "../requests/RequestDetail";
import {
  QUOTE_STATUS_LABELS,
  type QuoteStatus,
  type RecommendationTriageView,
  type RequestView,
} from "../requests/requestLabels";

type RequestsWorkspaceProps = {
  hidden: boolean;
  quotes: OperationsQuote[];
  onQuotesChange: Dispatch<SetStateAction<OperationsQuote[]>>;
  products: OperationsProduct[];
  privileged: boolean;
  requestView: RequestView;
  onRequestViewChange: (view: RequestView) => void;
  triageView: RecommendationTriageView;
  onTriageViewChange: (view: RecommendationTriageView) => void;
  selectedQuoteId: string | null;
  onSelectQuote: (quoteId: string) => void;
  /** A status change alters Overview's counts; the page refetches them. */
  onStatusSaved: () => void;
  onReplied: (thread: OperationsCommunicationThreadDetail) => void;
  onOpenThreadInInbox: (threadId: string) => void;
} & OperationsNoticeProps;

export function RequestsWorkspace({
  hidden,
  quotes,
  onQuotesChange,
  products,
  privileged,
  requestView,
  onRequestViewChange,
  triageView,
  onTriageViewChange,
  selectedQuoteId,
  onSelectQuote,
  onStatusSaved,
  onReplied,
  onOpenThreadInInbox,
  onMessage: setMessage,
  onError: setError,
}: RequestsWorkspaceProps) {
  const [quoteNoteDrafts, setQuoteNoteDrafts] =
    useState<Record<string, string>>({});
  const [
    quoteNoteSaveStates,
    setQuoteNoteSaveStates,
  ] = useState<Record<string, SaveState>>({});

  const lifecycleQuotes = useMemo(() => {
    if (requestView === "all") {
      return quotes;
    }

    return quotes.filter((quote) =>
      requestView === "closed"
        ? quote.status === "closed"
        : quote.status !== "closed",
    );
  }, [quotes, requestView]);

  const visibleQuotes = useMemo(() => {
    if (triageView === "all") {
      return lifecycleQuotes;
    }

    return lifecycleQuotes.filter((quote) => {
      if (triageView === "guided") {
        return quote.recommendation_context !== null;
      }

      if (triageView === "human_review") {
        return quote.recommendation_decision?.human_review === true;
      }

      return (
        quote.recommendation_decision?.requires_third_party_lab === true
      );
    });
  }, [lifecycleQuotes, triageView]);

  // The request shown in the detail pane: the one picked in the queue, or the
  // first request in the current view when that pick is filtered out.
  const selectedRequestId = useMemo(() => {
    if (
      selectedQuoteId !== null
      && visibleQuotes.some((quote) => quote.id === selectedQuoteId)
    ) {
      return selectedQuoteId;
    }
    return visibleQuotes[0]?.id ?? null;
  }, [selectedQuoteId, visibleQuotes]);

  const requestCounts = useMemo(() => ({
    active: quotes.filter((quote) => quote.status !== "closed").length,
    closed: quotes.filter((quote) => quote.status === "closed").length,
    all: quotes.length,
  }), [quotes]);

  const recommendationTriageCounts = useMemo(() => ({
    all: lifecycleQuotes.length,
    guided: lifecycleQuotes.filter(
      (quote) => quote.recommendation_context !== null,
    ).length,
    human_review: lifecycleQuotes.filter(
      (quote) => quote.recommendation_decision?.human_review === true,
    ).length,
    lab_testing: lifecycleQuotes.filter(
      (quote) => (
        quote.recommendation_decision?.requires_third_party_lab === true
      ),
    ).length,
  }), [lifecycleQuotes]);

  function mergeFormalQuote(
    requestId: string,
    formalQuote: OperationsFormalQuote,
  ): void {
    onQuotesChange((current) => current.map((quote) => {
      if (quote.id !== requestId) {
        return quote;
      }

      const withoutRevision = quote.formal_quotes
        .filter((candidate) => candidate.id !== formalQuote.id)
        .map((candidate) => (
          formalQuote.status === "presented"
          && candidate.status === "presented"
            ? { ...candidate, status: "superseded" as const }
            : candidate
        ));

      return {
        ...quote,
        status: formalQuote.status === "presented" ? "quoted" : quote.status,
        formal_quotes: [...withoutRevision, formalQuote],
      };
    }));
  }

  async function saveQuoteStatus(
    quote: OperationsQuote,
    nextStatus: string,
  ) {
    setError(null);
    setMessage(null);

    try {
      const updated = await updateQuoteStatus(
        quote.id,
        nextStatus,
      );

      onQuotesChange((current) =>
        current.map((candidate) =>
          candidate.id === updated.id ? updated : candidate,
        ),
      );

      onStatusSaved();
      setMessage("Quote status updated.");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Quote status update failed.",
      );
    }
  }

  async function saveQuoteNotes(
    quote: OperationsQuote,
  ) {
    const draft =
      quoteNoteDrafts[quote.id]
      ?? quote.internal_notes
      ?? "";

    setError(null);
    setMessage(null);
    setQuoteNoteSaveStates((current) => ({
      ...current,
      [quote.id]: "saving",
    }));

    try {
      const normalized =
        draft.trim().length > 0
          ? draft
          : null;

      const updated =
        await updateQuoteNotes(
          quote.id,
          normalized,
        );

      onQuotesChange((current) =>
        current.map((candidate) =>
          candidate.id === updated.id
            ? updated
            : candidate,
        ),
      );

      setQuoteNoteDrafts((current) => ({
        ...current,
        [quote.id]:
          updated.internal_notes ?? "",
      }));

      setQuoteNoteSaveStates((current) => ({
        ...current,
        [quote.id]: "saved",
      }));

      setMessage(
        "Internal quote notes saved.",
      );

      window.setTimeout(() => {
        setQuoteNoteSaveStates((current) => ({
          ...current,
          [quote.id]: "idle",
        }));
      }, 1800);
    } catch (caught) {
      setQuoteNoteSaveStates((current) => ({
        ...current,
        [quote.id]: "idle",
      }));

      setError(
        caught instanceof Error
          ? caught.message
          : "Internal quote notes could not be saved.",
      );
    }
  }

  return (
    <section
      id="operations-panel-requests"
      className="operations-workspace-panel"
      aria-label="Customer requests"
      hidden={hidden}
    >
    <section
      id="quote-queue"
      className="operations-section operations-workspace-main"
    >
      <div className="operations-section-heading">
        <p className="eyebrow">Quote Queue</p>
        <h2>Customer requests</h2>
      </div>

      <div
        className="operations-request-tabs"
        role="group"
        aria-label="Customer request view"
      >
        {(["active", "closed", "all"] as RequestView[]).map(
          (option) => (
            <button
              key={option}
              type="button"
              className={requestView === option ? "is-active" : ""}
              aria-pressed={requestView === option}
              onClick={() => {
                onRequestViewChange(option);
              }}
            >
              {option === "active"
                ? "Active requests"
                : option === "closed"
                  ? "Closed requests"
                  : "All requests"}
              {" "}
              <span>{requestCounts[option]}</span>
            </button>
          ),
        )}
      </div>

      <div className="operations-request-filter-group">
        <span>Recommendation triage</span>
        <div
          className="operations-request-tabs"
          role="group"
          aria-label="Recommendation triage view"
        >
          {([
            ["all", "All"],
            ["guided", "Guided"],
            ["human_review", "Human review"],
            ["lab_testing", "Lab testing"],
          ] as const).map(([option, label]) => (
            <button
              key={option}
              type="button"
              className={
                triageView === option ? "is-active" : ""
              }
              aria-pressed={triageView === option}
              onClick={() => {
                onTriageViewChange(option);
              }}
            >
              {label}{" "}
              <span>{recommendationTriageCounts[option]}</span>
            </button>
          ))}
        </div>
      </div>

      {quotes.length === 0 ? (
        <p className="account-muted">No quote requests.</p>
      ) : visibleQuotes.length === 0 ? (
        <p className="account-muted">
          No customer requests in this view.
        </p>
      ) : (
        <div className="operations-request-split">
          <ul
            className="operations-request-queue"
            aria-label="Requests in this view"
          >
            {visibleQuotes.map((quote) => {
              const selected = quote.id === selectedRequestId;
              const needs =
                quote.recommendation_decision?.title
                ?? quote.product_name
                ?? "General consultation";
              return (
                <li key={quote.id}>
                  <button
                    type="button"
                    className={
                      "operations-request-queue-item"
                      + (selected ? " is-selected" : "")
                    }
                    aria-current={selected ? "true" : undefined}
                    aria-controls={`operations-request-${quote.id}`}
                    onClick={() => {
                      onSelectQuote(quote.id);
                    }}
                  >
                    <span className="operations-request-queue-top">
                      <strong>{quote.name}</strong>
                      <time
                        dateTime={quote.created_at}
                        title={new Date(quote.created_at).toLocaleString()}
                      >
                        {formatRequestAge(quote.created_at)}
                      </time>
                    </span>
                    <span className="operations-request-queue-need">
                      {needs}
                    </span>
                    <span className="operations-request-queue-tags">
                      <span
                        className="operations-request-tag"
                        data-status={quote.status}
                      >
                        {QUOTE_STATUS_LABELS[quote.status as QuoteStatus] ?? quote.status}
                      </span>
                      {quote.recommendation_decision?.human_review === true ? (
                        <span className="operations-request-tag">
                          Human review
                        </span>
                      ) : null}
                      {quote.recommendation_decision?.requires_third_party_lab === true ? (
                        <span className="operations-request-tag is-important">
                          Lab testing
                        </span>
                      ) : null}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
          <div className="operations-request-detail">
          {visibleQuotes.map((quote) => (
            <RequestDetail
              key={quote.id}
              quote={quote}
              products={products}
              privileged={privileged}
              selected={quote.id === selectedRequestId}
              active={!hidden && quote.id === selectedRequestId}
              noteDraft={quoteNoteDrafts[quote.id] ?? quote.internal_notes ?? ""}
              noteSaveState={quoteNoteSaveStates[quote.id] ?? "idle"}
              onNoteDraftChange={(value) => {
                setQuoteNoteDrafts((current) => ({
                  ...current,
                  [quote.id]: value,
                }));
              }}
              onSaveNotes={() => {
                void saveQuoteNotes(quote);
              }}
              onSaveStatus={(status) => {
                void saveQuoteStatus(quote, status);
              }}
              onFormalQuoteChange={mergeFormalQuote}
              onReplied={onReplied}
              onOpenThreadInInbox={onOpenThreadInInbox}
            />
          ))}
          </div>
        </div>
      )}
    </section>

    </section>
  );
}
