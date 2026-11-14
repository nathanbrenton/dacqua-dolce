import { useEffect, useState } from "react";

import {
  getOperationsQuoteConversation,
  replyToOperationsQuoteConversation,
  type OperationsCommunicationReply,
  type OperationsQuote,
  type OperationsQuoteConversation,
} from "../../api/operations";
import {
  ConversationMessageList,
  ConversationReplyForm,
} from "./ConversationThread";

// How many of the latest emails a request shows before "Show earlier".
const RECENT_EMAILS = 3;

type RequestConversationProps = {
  quote: OperationsQuote;
  // Only the selected request loads its conversation.
  active: boolean;
  onReplied?: (reply: OperationsCommunicationReply) => void;
  onOpenInInbox?: (threadId: string) => void;
};

/**
 * The customer email conversation linked to a request, with a reply box.
 * With no conversation yet, the first reply starts one (linked to the request
 * and filed in the Inbox).
 */
export function RequestConversation({
  quote,
  active,
  onReplied,
  onOpenInInbox,
}: RequestConversationProps) {
  const [conversation, setConversation] =
    useState<OperationsQuoteConversation | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);

  async function load(): Promise<void> {
    setLoading(true);
    setError(null);

    try {
      setConversation(await getOperationsQuoteConversation(quote.id));
      setLoaded(true);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Conversation could not be loaded.",
      );
    } finally {
      setLoading(false);
    }
  }

  // Load the first time the request is opened; "Refresh" picks up new mail.
  useEffect(() => {
    if (active && !loaded && !loading) {
      void load();
    }
    // load() only depends on quote.id, which is stable per mounted request.
  }, [active, loaded]);

  async function sendReply(
    body: string,
    recipient: string,
    sender: string,
  ): Promise<OperationsCommunicationReply> {
    const result = await replyToOperationsQuoteConversation(
      quote.id,
      body,
      recipient,
      sender,
    );

    setConversation({
      thread: result.thread,
      reply_target: result.thread.reply_target,
      reply_target_source: result.thread.reply_target_source,
      reply_sender_addresses: result.thread.reply_sender_addresses,
      reply_sender_default: result.thread.reply_sender_default,
    });
    onReplied?.(result);

    return result;
  }

  const thread = conversation?.thread ?? null;
  const messageCount = thread?.messages.length ?? 0;

  // Long threads show the latest few emails; earlier ones are one click away.
  // (No inner scroll box: it trapped the mouse wheel inside the request.)
  const hiddenCount = showAll ? 0 : Math.max(0, messageCount - RECENT_EMAILS);
  const visibleMessages = thread?.messages.slice(hiddenCount) ?? [];

  return (
    <section
      className="operations-request-region operations-request-conversation"
      aria-busy={loading}
    >
      <div className="operations-request-region-heading">
        <p className="operations-request-region-label">Conversation</p>
        <span className="operations-request-conversation-tools">
          {thread !== null ? (
            <span>
              {messageCount}
              {messageCount === 1 ? " email" : " emails"}
              {thread.status === "closed" ? " · archived" : ""}
            </span>
          ) : null}
          <button
            type="button"
            className="operations-action secondary compact"
            disabled={loading}
            onClick={() => {
              void load();
            }}
          >
            {loading && loaded ? "Refreshing…" : "Refresh"}
          </button>
          {thread !== null && onOpenInInbox !== undefined ? (
            <button
              type="button"
              className="operations-action secondary compact"
              onClick={() => {
                onOpenInInbox(thread.id);
              }}
            >
              Open in Inbox
            </button>
          ) : null}
        </span>
      </div>

      {error !== null ? (
        <p className="operations-alert operations-error" role="alert">
          {error}
        </p>
      ) : null}

      {!loaded ? (
        loading ? (
          <p className="account-muted">Loading conversation…</p>
        ) : null
      ) : conversation === null ? null : (
        <>
          {thread !== null && thread.messages.length > 0 ? (
            <div
              className="operations-request-conversation-messages"
              aria-label="Emails with this customer"
            >
              {hiddenCount > 0 ? (
                <button
                  type="button"
                  className="operations-action secondary compact operations-request-earlier"
                  onClick={() => {
                    setShowAll(true);
                  }}
                >
                  Show {hiddenCount} earlier
                  {hiddenCount === 1 ? " email" : " emails"}
                </button>
              ) : null}
              <ConversationMessageList
                messages={visibleMessages}
                label={null}
              />
            </div>
          ) : (
            <p className="operations-request-empty">
              No emails with this customer yet. Your first reply starts the
              conversation; their answers come back here and in the Inbox.
            </p>
          )}

          <ConversationReplyForm
            heading={thread === null ? "Email the customer" : "Reply"}
            senderAddresses={conversation.reply_sender_addresses}
            defaultSender={conversation.reply_sender_default}
            defaultRecipient={conversation.reply_target}
            recipientSource={conversation.reply_target_source}
            accountEmail={thread?.customer_email ?? null}
            closedHint={
              thread?.status === "closed"
                ? "This conversation is archived. Restore it in the Inbox before replying."
                : null
            }
            onSubmit={sendReply}
          />
        </>
      )}
    </section>
  );
}
