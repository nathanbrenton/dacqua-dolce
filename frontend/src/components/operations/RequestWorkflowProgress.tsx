import type {
  OperationsFormalQuote,
  OperationsQuote,
} from "../../api/operations";

// The whole life of a customer request, from the request arriving to it being
// closed. Each step is worked out from the request and its formal quotes, so
// the bar shows where the request really is, not only its status field.

type QuoteRequestStatus = "new" | "contacted" | "quoted" | "closed";

type WorkflowStepId =
  | "received"
  | "contacted"
  | "drafted"
  | "staff_review"
  | "presented"
  | "approved"
  | "closed";

type WorkflowStep = {
  id: WorkflowStepId;
  label: string;
  done: boolean;
};

type NextStep = {
  hint: string;
  action:
    | { kind: "status"; label: string; status: QuoteRequestStatus }
    | { kind: "quote"; label: string }
    | null;
};

function latestFormalQuote(
  formalQuotes: OperationsFormalQuote[],
): OperationsFormalQuote | null {
  const current = formalQuotes.filter((quote) => quote.status !== "superseded");
  if (current.length === 0) {
    return null;
  }
  return current.reduce((latest, quote) =>
    quote.revision_number > latest.revision_number ? quote : latest,
  );
}

function workflowSteps(quote: OperationsQuote): WorkflowStep[] {
  const latest = latestFormalQuote(quote.formal_quotes);
  const anyPresented = quote.formal_quotes.some(
    (formalQuote) =>
      formalQuote.status === "presented" || formalQuote.status === "approved",
  );
  const approved = quote.formal_quotes.some(
    (formalQuote) => formalQuote.status === "approved",
  );
  const closed = quote.status === "closed";

  const steps: WorkflowStep[] = [
    { id: "received", label: "Received", done: true },
    {
      id: "contacted",
      label: "Contacted",
      done: quote.status !== "new" || latest !== null,
    },
    { id: "drafted", label: "Quote drafted", done: latest !== null },
  ];

  if (latest?.staff_review_required === true) {
    steps.push({
      id: "staff_review",
      label: "Staff review",
      done: latest.staff_review_completed_at !== null || anyPresented,
    });
  }

  steps.push(
    {
      id: "presented",
      label: "Presented",
      done: anyPresented || quote.status === "quoted",
    },
    { id: "approved", label: "Customer approved", done: approved },
    { id: "closed", label: "Closed", done: closed },
  );

  return steps;
}

function nextStepFor(
  stepId: WorkflowStepId | null,
  quote: OperationsQuote,
): NextStep {
  switch (stepId) {
    case "contacted":
      return {
        hint: "Email the customer from the Conversation section below (sending marks it contacted), or call them and mark it contacted.",
        action: { kind: "status", label: "Mark as contacted", status: "contacted" },
      };
    case "drafted":
      return {
        hint: "Build a formal quote for this request.",
        action: { kind: "quote", label: "Start quote" },
      };
    case "staff_review":
      return {
        hint: "This quote needs staff review before it can be presented.",
        action: { kind: "quote", label: "Go to staff review" },
      };
    case "presented":
      return {
        hint:
          `Present the quote. The customer needs an account using ${quote.email}, `
          + "and the quote needs delivery and billing addresses.",
        action: { kind: "quote", label: "Go to quote" },
      };
    case "approved":
      return {
        hint:
          "Waiting for the customer to approve the quote in their account. "
          + "Approving creates the order.",
        action: null,
      };
    case "closed":
      return {
        hint: "The customer approved and the order was created. Close the request when you're done.",
        action: { kind: "status", label: "Close request", status: "closed" },
      };
    default:
      return {
        hint: "This request is closed.",
        action: { kind: "status", label: "Reopen request", status: "contacted" },
      };
  }
}

export function RequestWorkflowProgress({
  quote,
  onSetStatus,
  onOpenQuote,
}: {
  quote: OperationsQuote;
  onSetStatus: (status: QuoteRequestStatus) => void;
  onOpenQuote: () => void;
}) {
  const steps = workflowSteps(quote);
  const closed = quote.status === "closed";
  // A closed request has no current step; earlier steps that never happened
  // read as skipped rather than pending.
  const currentStep = closed
    ? null
    : steps.find((step) => !step.done) ?? null;
  const nextStep = nextStepFor(currentStep?.id ?? null, quote);
  const doneCount = steps.filter((step) => step.done).length;

  return (
    <div className="operations-request-workflow">
      <ol
        className="operations-workflow-track"
        aria-label={`Request progress: ${doneCount} of ${steps.length} steps done`}
      >
        {steps.map((step) => {
          const state = step.done
            ? "done"
            : step.id === currentStep?.id
              ? "current"
              : closed
                ? "skipped"
                : "upcoming";
          return (
            <li
              key={step.id}
              className={`operations-workflow-step is-${state}`}
              aria-current={state === "current" ? "step" : undefined}
            >
              <span className="operations-workflow-node" aria-hidden="true" />
              <span className="operations-workflow-label">
                {step.label}
                <span className="sr-only">
                  {state === "done"
                    ? " (done)"
                    : state === "current"
                      ? " (current step)"
                      : state === "skipped"
                        ? " (skipped)"
                        : ""}
                </span>
              </span>
            </li>
          );
        })}
      </ol>

      <div className="operations-request-next">
        <p>
          <strong>Next:</strong> {nextStep.hint}
        </p>
        <div className="operations-request-next-actions">
          {nextStep.action !== null ? (
            <button
              type="button"
              className="operations-action"
              onClick={() => {
                const action = nextStep.action;
                if (action === null) {
                  return;
                }
                if (action.kind === "quote") {
                  onOpenQuote();
                } else {
                  onSetStatus(action.status);
                }
              }}
            >
              {nextStep.action.label}
            </button>
          ) : null}
          {!closed
          && !(
            nextStep.action?.kind === "status"
            && nextStep.action.status === "closed"
          ) ? (
            <button
              type="button"
              className="operations-action secondary"
              onClick={() => {
                onSetStatus("closed");
              }}
            >
              Close request
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
