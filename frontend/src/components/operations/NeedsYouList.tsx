import type {
  OperationsCommunicationThread,
  OperationsOrder,
  OperationsQuote,
} from "../../api/operations";
import { formatRequestAge } from "./formatRequestAge";
import { orderNextStep, requestNextStepSummary } from "./operationsNextSteps";

// The Overview's work list: every item whose next move is the operator's,
// oldest first, each opening straight to that item. Items waiting on someone
// else (customer, supplier, carrier) are listed separately.

type NeedsYouKind = "request" | "email" | "order" | "delivery";

type NeedsYouItem = {
  key: string;
  kind: NeedsYouKind;
  who: string;
  action: string;
  // When the item started waiting; null sorts last.
  since: string | null;
  important?: boolean;
  open: () => void;
};

const KIND_LABELS: Record<NeedsYouKind, string> = {
  request: "Request",
  email: "Email",
  order: "Order",
  delivery: "Email delivery",
};

function orderCustomerName(order: OperationsOrder): string {
  const name = [order.customer.first_name, order.customer.last_name]
    .filter((value): value is string => value !== null && value.trim() !== "")
    .join(" ");
  return name || order.customer.email;
}

function sinceTime(item: NeedsYouItem): number {
  return item.since === null ? Number.POSITIVE_INFINITY : new Date(item.since).getTime();
}

function NeedsYouRows({ items }: { items: NeedsYouItem[] }) {
  return (
    <ul className="operations-needs-you-list">
      {items.map((item) => (
        <li key={item.key}>
          <button
            type="button"
            className={
              "operations-needs-you-item"
              + (item.important === true ? " is-important" : "")
            }
            onClick={item.open}
          >
            <span className="operations-needs-you-kind" data-kind={item.kind}>
              {KIND_LABELS[item.kind]}
            </span>
            <span className="operations-needs-you-text">
              <strong>{item.action}</strong>
              <span>{item.who}</span>
            </span>
            {item.since !== null ? (
              <time
                dateTime={item.since}
                title={new Date(item.since).toLocaleString()}
              >
                {formatRequestAge(item.since)}
              </time>
            ) : (
              <span aria-hidden="true" />
            )}
            <span className="operations-needs-you-go" aria-hidden="true">→</span>
          </button>
        </li>
      ))}
    </ul>
  );
}

export function NeedsYouList({
  quotes,
  orders,
  awaitingReplyThreads,
  failedDeliveryCount,
  latestFailedDeliveryAt,
  onOpenRequest,
  onOpenThread,
  onOpenOrder,
  onOpenDeliveryIssues,
}: {
  quotes: OperationsQuote[];
  orders: OperationsOrder[];
  // Open Inbox conversations whose latest message is from the customer.
  awaitingReplyThreads: OperationsCommunicationThread[];
  failedDeliveryCount: number;
  latestFailedDeliveryAt: string | null;
  onOpenRequest: (quoteId: string) => void;
  onOpenThread: (threadId: string) => void;
  onOpenOrder: (orderId: string) => void;
  onOpenDeliveryIssues: () => void;
}) {
  const needsYou: NeedsYouItem[] = [];
  const waiting: NeedsYouItem[] = [];

  for (const quote of quotes) {
    const next = requestNextStepSummary(quote);
    if (next === null) {
      continue;
    }
    const lab = quote.recommendation_decision?.requires_third_party_lab === true;
    const review = quote.recommendation_decision?.human_review === true;
    const item: NeedsYouItem = {
      key: `request-${quote.id}`,
      kind: "request",
      who:
        quote.name
        + (lab ? " · lab testing" : review ? " · human review" : ""),
      action: next.label,
      since: quote.created_at,
      important: lab,
      open: () => {
        onOpenRequest(quote.id);
      },
    };
    (next.waiting ? waiting : needsYou).push(item);
  }

  for (const thread of awaitingReplyThreads) {
    needsYou.push({
      key: `email-${thread.id}`,
      kind: "email",
      who:
        (thread.customer_email ?? thread.latest_sender_address ?? "Unknown sender")
        + " · "
        + (thread.latest_subject ?? thread.subject ?? "No subject"),
      action: "Reply to the customer",
      since: thread.last_message_at ?? thread.created_at,
      open: () => {
        onOpenThread(thread.id);
      },
    });
  }

  for (const order of orders) {
    const next = orderNextStep(order);
    if (next === null) {
      continue;
    }
    const item: NeedsYouItem = {
      key: `order-${order.id}`,
      kind: "order",
      who: orderCustomerName(order),
      action: next.action,
      since: order.created_at,
      important: next.important,
      open: () => {
        onOpenOrder(order.id);
      },
    };
    (next.waiting ? waiting : needsYou).push(item);
  }

  if (failedDeliveryCount > 0) {
    needsYou.push({
      key: "delivery-failures",
      kind: "delivery",
      who:
        `${failedDeliveryCount} failed `
        + (failedDeliveryCount === 1 ? "email" : "emails"),
      action: "Check failed email deliveries",
      since: latestFailedDeliveryAt,
      open: onOpenDeliveryIssues,
    });
  }

  needsYou.sort((left, right) => sinceTime(left) - sinceTime(right));
  waiting.sort((left, right) => sinceTime(left) - sinceTime(right));

  return (
    <section
      className="operations-section operations-needs-you"
      aria-labelledby="operations-needs-you-title"
    >
      <div className="operations-needs-you-heading">
        <h2 id="operations-needs-you-title">Needs you</h2>
        <span>
          {needsYou.length === 0
            ? "All caught up"
            : `${needsYou.length} ${needsYou.length === 1 ? "item" : "items"}, oldest first`}
        </span>
      </div>

      {needsYou.length === 0 ? (
        <p className="operations-needs-you-empty">
          Nothing is waiting on you right now.
        </p>
      ) : (
        <NeedsYouRows items={needsYou} />
      )}

      {waiting.length > 0 ? (
        <details className="operations-needs-you-waiting">
          <summary>
            Waiting on someone else
            {" "}
            <span>{waiting.length}</span>
          </summary>
          <NeedsYouRows items={waiting} />
        </details>
      ) : null}
    </section>
  );
}
