// Next-step rules for requests and orders, shared by the request progress bar
// and the Overview's "Needs you" list. Plain TypeScript (no JSX) so the
// frontend tests can import it directly.
import type {
  OperationsFormalQuote,
  OperationsOrder,
  OperationsQuote,
} from "../../api/operations";

// The whole life of a customer request, from the request arriving to it being
// closed. Each step is worked out from the request and its formal quotes, so
// the bar shows where the request really is, not only its status field.

export type QuoteRequestStatus = "new" | "contacted" | "quoted" | "closed";

export type WorkflowStepId =
  | "received"
  | "contacted"
  | "drafted"
  | "staff_review"
  | "presented"
  | "approved"
  | "closed";

export type WorkflowStep = {
  id: WorkflowStepId;
  label: string;
  done: boolean;
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

export function workflowSteps(quote: OperationsQuote): WorkflowStep[] {
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

/**
 * The request's next step in a few words, for the Overview's "Needs you"
 * list. `waiting` is true when the next move is the customer's. Null for a
 * closed request.
 */
export function requestNextStepSummary(
  quote: OperationsQuote,
): { label: string; waiting: boolean } | null {
  if (quote.status === "closed") {
    return null;
  }
  const current = workflowSteps(quote).find((step) => !step.done);
  switch (current?.id) {
    case "contacted":
      return { label: "Contact the customer", waiting: false };
    case "drafted":
      return { label: "Build a formal quote", waiting: false };
    case "staff_review":
      return { label: "Staff review the quote", waiting: false };
    case "presented":
      return { label: "Present the quote", waiting: false };
    case "approved":
      return { label: "Waiting for the customer to approve the quote", waiting: true };
    default:
      return { label: "Close the request", waiting: false };
  }
}

/** An order's next step, and whether that step is someone else's. */
export function orderNextStep(
  order: OperationsOrder,
): { action: string; waiting: boolean; important?: boolean } | null {
  if (
    order.status !== "paid"
    || order.customer_status === "cancelled"
    || order.customer_status === "refunded"
    || order.fulfillment_status === "delivered"
  ) {
    return null;
  }
  if (order.cancellation?.status === "requested") {
    return { action: "Review the cancellation request", waiting: false, important: true };
  }
  if (order.cancellation?.status === "approved") {
    return { action: "Finish the approved cancellation", waiting: false };
  }
  if (order.review.on_hold) {
    return { action: "On hold, waiting for the customer", waiting: true };
  }
  if (order.review.status === "pending") {
    return { action: "Review the order", waiting: false };
  }
  if (order.order_confirmation.status === "failed") {
    return { action: "Resend the order confirmation", waiting: false, important: true };
  }
  switch (order.fulfillment_status) {
    case "not_started":
      return { action: "Order from the supplier", waiting: false };
    case "supplier_ordered":
      return { action: "Waiting for the supplier", waiting: true };
    case "received_ready":
      return { action: "Ship the order", waiting: false };
    case "shipped":
      return { action: "Shipped, waiting for delivery", waiting: true };
    default:
      return null;
  }
}
