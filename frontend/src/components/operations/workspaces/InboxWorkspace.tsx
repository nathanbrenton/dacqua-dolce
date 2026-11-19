// Inbox workspace of Operations: failed email deliveries still needing a look
// (only when there are any) and the customer inbox (../CommunicationsInbox.tsx).
//
// Failed deliveries come from OperationsPage (Overview's "Needs you" counts
// them too); marking them reviewed hands the updated rows back through
// onDeliveriesReviewed.
//
// API: reviewOperationsCommunications in api/operations.ts
//   -> POST /api/operations/communications/review
// Styles: .operations-delivery-issue*, .operations-inbox* in styles.css

import { useState } from "react";

import {
  reviewOperationsCommunications,
  type OperationsCommunication,
  type OperationsCommunicationThread,
  type OperationsCommunicationThreadDetail,
} from "../../../api/operations";
import { CommunicationsInbox } from "../CommunicationsInbox";
import type { OperationsNoticeProps } from "../operationsShared";

type InboxWorkspaceProps = {
  hidden: boolean;
  failedDeliveries: OperationsCommunication[];
  onDeliveriesReviewed: (reviewed: OperationsCommunication[]) => void;
  onActiveCountChange: (count: number) => void;
  onAwaitingReplyChange: (threads: OperationsCommunicationThread[]) => void;
  onOpenRequest: (quoteId: string) => void;
  threadToOpen: { threadId: string } | null;
  updatedThread: OperationsCommunicationThreadDetail | null;
} & OperationsNoticeProps;

export function InboxWorkspace({
  hidden,
  failedDeliveries,
  onDeliveriesReviewed,
  onActiveCountChange,
  onAwaitingReplyChange,
  onOpenRequest,
  threadToOpen,
  updatedThread,
  onMessage: setMessage,
  onError: setError,
}: InboxWorkspaceProps) {
  const [reviewingDeliveryIds, setReviewingDeliveryIds] =
    useState<string[]>([]);

  async function markDeliveriesReviewed(deliveryIds: string[]): Promise<void> {
    setReviewingDeliveryIds(deliveryIds);
    setError(null);
    try {
      const reviewed = await reviewOperationsCommunications(deliveryIds);
      onDeliveriesReviewed(reviewed);
      setMessage(
        deliveryIds.length === 1
          ? "Failed email marked reviewed."
          : `${deliveryIds.length} failed emails marked reviewed.`,
      );
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to mark the failed emails reviewed.",
      );
    } finally {
      setReviewingDeliveryIds([]);
    }
  }

  return (
    <section
      id="operations-panel-communications"
      className="operations-workspace-panel"
      aria-label="Communications"
      hidden={hidden}
    >
    {failedDeliveries.length > 0 ? (
      <details
        id="email-delivery-issues"
        className="operations-section operations-disclosure"
      >
        <summary className="operations-disclosure-summary">
          <span>
            <strong>Delivery issues</strong>
            <small>Failed email deliveries</small>
          </span>
        </summary>
        <div className="operations-disclosure-content">
          <section
            className="operations-delivery-issues"
            aria-labelledby="email-delivery-issues-title"
          >
        <div className="operations-delivery-issues-heading">
          <p className="eyebrow">Delivery Issues</p>
          <h2 id="email-delivery-issues-title">Failed email deliveries</h2>
          <p className="account-muted">
            Once you've dealt with a failed email (or it no longer matters),
            mark it reviewed to clear it from here and from Needs you.
          </p>
          {failedDeliveries.length > 1 ? (
            <button
              type="button"
              className="operations-action secondary compact"
              disabled={reviewingDeliveryIds.length > 0}
              onClick={() => {
                void markDeliveriesReviewed(
                  failedDeliveries.map((delivery) => delivery.id),
                );
              }}
            >
              Mark all {failedDeliveries.length} reviewed
            </button>
          ) : null}
        </div>
        <div className="operations-delivery-issue-list">
          {failedDeliveries.map((delivery) => (
            <article key={delivery.id}>
              <span className="operations-status-badge is-failed">
                Failed
              </span>
              <strong>{delivery.subject}</strong>
              <span>{delivery.recipient}</span>
              <small>
                {delivery.category.replaceAll("_", " ")}
                {" · "}
                {new Date(delivery.created_at).toLocaleString()}
              </small>
              <button
                type="button"
                className="operations-action secondary compact"
                disabled={reviewingDeliveryIds.length > 0}
                onClick={() => {
                  void markDeliveriesReviewed([delivery.id]);
                }}
              >
                {reviewingDeliveryIds.includes(delivery.id)
                  ? "Saving…"
                  : "Mark reviewed"}
              </button>
            </article>
          ))}
        </div>
          </section>
        </div>
      </details>
    ) : null}

    <section
      id="communications-history"
      className="operations-section operations-customer-inbox-section operations-workspace-main"
    >
      <CommunicationsInbox
        onActiveCountChange={onActiveCountChange}
        onOpenRequest={onOpenRequest}
        onAwaitingReplyChange={onAwaitingReplyChange}
        threadToOpen={threadToOpen}
        updatedThread={updatedThread}
      />
    </section>

    </section>
  );
}
