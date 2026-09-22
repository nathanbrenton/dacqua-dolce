import {
  type FormEvent,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getOperationsCommunicationThread,
  getOperationsCommunicationThreads,
  replyToOperationsCommunicationThread,
  type OperationsCommunicationMessage,
  type OperationsCommunicationThread,
  type OperationsCommunicationThreadDetail,
} from "../../api/operations";

function formatTimestamp(value: string | null): string {
  if (value === null) {
    return "No message timestamp";
  }

  return new Date(value).toLocaleString();
}

function formatBytes(value: number): string {
  if (value < 1024) {
    return `${value} B`;
  }

  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }

  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function messageTimestamp(
  message: OperationsCommunicationMessage,
): string {
  return (
    message.received_at
    ?? message.sent_at
    ?? message.created_at
  );
}

function threadSearchText(
  thread: OperationsCommunicationThread,
): string {
  return [
    thread.id,
    thread.customer_email ?? "",
    thread.subject ?? "",
    thread.latest_subject ?? "",
    thread.latest_sender_address ?? "",
    thread.latest_direction ?? "",
    thread.status,
    thread.related_entity_type ?? "",
    thread.related_entity_id ?? "",
  ]
    .join(" ")
    .toLowerCase();
}

function recipientLabel(
  message: OperationsCommunicationMessage,
): string {
  const recipients = message.recipients
    .filter((recipient) => recipient.recipient_type === "to")
    .map((recipient) => recipient.address);

  if (recipients.length === 0) {
    return "No To recipient archived";
  }

  return recipients.join(", ");
}

function relatedRecordLabel(
  type: string | null,
): string | null {
  if (type === null) {
    return null;
  }

  const labels: Record<string, string> = {
    quote_request: "Quote request",
    user: "Customer account",
    order: "Customer order",
  };

  return labels[type] ?? "Related record";
}

function deliveryNotice(status: string): string {
  if (status === "sent") {
    return "Reply sent and archived.";
  }

  if (status === "suppressed") {
    return "Reply archived locally; email delivery is disabled in this environment.";
  }

  return "Reply attempt was archived, but email delivery failed.";
}

export function CommunicationsInbox() {
  const [threads, setThreads] =
    useState<OperationsCommunicationThread[]>([]);
  const [selectedThreadId, setSelectedThreadId] =
    useState<string | null>(null);
  const [threadDetail, setThreadDetail] =
    useState<OperationsCommunicationThreadDetail | null>(null);
  const [search, setSearch] = useState("");
  const [replyBody, setReplyBody] = useState("");
  const [replyNotice, setReplyNotice] = useState<string | null>(null);
  const [replyFailed, setReplyFailed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [replySending, setReplySending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    void getOperationsCommunicationThreads()
      .then((result) => {
        if (!cancelled) {
          setThreads(result);
          setError(null);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(
            caught instanceof Error
              ? caught.message
              : "Communication threads could not be loaded.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const filteredThreads = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (query.length === 0) {
      return threads;
    }

    return threads.filter((thread) =>
      threadSearchText(thread).includes(query),
    );
  }, [search, threads]);

  async function openThread(threadId: string): Promise<void> {
    setSelectedThreadId(threadId);
    setDetailLoading(true);
    setReplyBody("");
    setReplyNotice(null);
    setReplyFailed(false);
    setError(null);

    try {
      const result = await getOperationsCommunicationThread(threadId);
      setThreadDetail(result);
    } catch (caught) {
      setThreadDetail(null);
      setError(
        caught instanceof Error
          ? caught.message
          : "Conversation could not be loaded.",
      );
    } finally {
      setDetailLoading(false);
    }
  }

  async function submitReply(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    if (threadDetail === null || replyBody.trim().length === 0) {
      return;
    }

    setReplySending(true);
    setReplyNotice(null);
    setReplyFailed(false);
    setError(null);

    try {
      const result = await replyToOperationsCommunicationThread(
        threadDetail.id,
        replyBody,
      );

      setThreadDetail(result.thread);
      setThreads((current) =>
        current
          .map((thread) =>
            thread.id === result.thread.id
              ? result.thread
              : thread,
          )
          .sort((left, right) => {
            const leftTime = new Date(
              left.last_message_at ?? left.created_at,
            ).getTime();
            const rightTime = new Date(
              right.last_message_at ?? right.created_at,
            ).getTime();

            return rightTime - leftTime;
          }),
      );
      setReplyNotice(deliveryNotice(result.delivery_status));
      setReplyFailed(result.delivery_status === "failed");

      if (result.delivery_status !== "failed") {
        setReplyBody("");
      }
    } catch (caught) {
      setReplyFailed(true);
      setReplyNotice(
        caught instanceof Error
          ? caught.message
          : "Reply could not be submitted.",
      );
    } finally {
      setReplySending(false);
    }
  }

  return (
    <div className="operations-inbox">
      <div className="operations-section-heading">
        <p className="eyebrow">Customer Communications</p>
        <h2>Conversation inbox</h2>
        <p>
          Search the durable customer email archive, inspect a
          conversation, and reply from the same thread.
        </p>
      </div>

      <label
        className="operations-field operations-customer-search"
      >
        <span>Search conversations</span>
        <input
          type="search"
          placeholder="Customer, sender, subject, status, related record…"
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
          }}
        />
      </label>

      {error !== null ? (
        <p className="operations-alert operations-error">
          {error}
        </p>
      ) : null}

      <div className="operations-inbox-layout">
        <div
          className="operations-inbox-thread-list"
          aria-label="Communication threads"
        >
          {loading ? (
            <p className="account-muted">Loading conversations…</p>
          ) : threads.length === 0 ? (
            <p className="account-muted">
              No archived conversations yet.
            </p>
          ) : filteredThreads.length === 0 ? (
            <p className="account-muted">
              No conversations match this search.
            </p>
          ) : (
            filteredThreads.map((thread) => (
              <button
                key={thread.id}
                type="button"
                className={
                  "operations-inbox-thread "
                  + (
                    selectedThreadId === thread.id
                      ? "is-selected"
                      : ""
                  )
                }
                aria-pressed={selectedThreadId === thread.id}
                onClick={() => {
                  void openThread(thread.id);
                }}
              >
                <span className="operations-inbox-thread-meta">
                  {thread.latest_direction ?? "conversation"}
                  {" · "}
                  {thread.status}
                  {" · "}
                  {thread.message_count}
                  {thread.message_count === 1 ? " message" : " messages"}
                </span>

                <strong>
                  {thread.latest_subject
                    ?? thread.subject
                    ?? "Untitled conversation"}
                </strong>

                <span>
                  {thread.customer_email
                    ?? thread.latest_sender_address
                    ?? "Unmatched sender"}
                </span>

                <small>
                  {formatTimestamp(
                    thread.last_message_at ?? thread.created_at,
                  )}
                </small>
              </button>
            ))
          )}
        </div>

        <section
          className="operations-inbox-conversation"
          aria-live="polite"
        >
          {selectedThreadId === null ? (
            <div className="operations-inbox-empty">
              <strong>Select a conversation</strong>
              <p>
                Choose a thread to inspect its archived inbound and
                outbound messages.
              </p>
            </div>
          ) : detailLoading ? (
            <p className="account-muted">Loading conversation…</p>
          ) : threadDetail === null ? (
            <p className="account-muted">
              Conversation details are unavailable.
            </p>
          ) : (
            <>
              <header className="operations-inbox-conversation-header">
                <p className="product-meta">
                  {threadDetail.status}
                  {" · "}
                  {threadDetail.messages.length}
                  {threadDetail.messages.length === 1
                    ? " message"
                    : " messages"}
                </p>
                <h3>
                  {threadDetail.subject
                    ?? threadDetail.latest_subject
                    ?? "Untitled conversation"}
                </h3>
                {threadDetail.customer_email !== null ? (
                  <p>{threadDetail.customer_email}</p>
                ) : (
                  <span className="operations-inbox-unmatched">
                    Unmatched sender
                  </span>
                )}
                {relatedRecordLabel(
                  threadDetail.related_entity_type,
                ) !== null ? (
                  <small className="operations-inbox-related">
                    {relatedRecordLabel(
                      threadDetail.related_entity_type,
                    )}
                  </small>
                ) : null}
              </header>

              <div className="operations-inbox-message-list">
                {threadDetail.messages.map((message) => (
                  <article
                    key={message.id}
                    className={
                      "operations-inbox-message "
                      + `is-${message.direction}`
                    }
                  >
                    <header>
                      <div>
                        <span
                          className={
                            "operations-inbox-direction "
                            + `is-${message.direction}`
                          }
                        >
                          {message.direction}
                        </span>
                        <strong>
                          {message.sender_name !== null
                            ? `${message.sender_name} <${message.sender_address}>`
                            : message.sender_address}
                        </strong>
                      </div>
                      <small>
                        {formatTimestamp(messageTimestamp(message))}
                      </small>
                    </header>

                    <p className="operations-inbox-recipient">
                      To: {recipientLabel(message)}
                    </p>

                    <h4>{message.subject}</h4>

                    <div className="operations-inbox-body">
                      {message.content_redacted ? (
                        <em>
                          Sensitive message content is redacted from
                          the archive.
                        </em>
                      ) : message.body_text !== null
                        && message.body_text.trim().length > 0 ? (
                          <p>{message.body_text}</p>
                        ) : (
                          <em>No plain-text body archived.</em>
                        )}
                    </div>

                    {message.attachments.length > 0 ? (
                      <div className="operations-inbox-attachments">
                        <strong>Attachments</strong>
                        <ul>
                          {message.attachments.map((attachment) => (
                            <li key={attachment.id}>
                              <span>{attachment.filename}</span>
                              <small>
                                {attachment.content_type}
                                {" · "}
                                {formatBytes(attachment.size_bytes)}
                              </small>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : null}
                  </article>
                ))}
              </div>

              <form
                className="operations-inbox-reply"
                onSubmit={(event) => {
                  void submitReply(event);
                }}
              >
                <div>
                  <strong>Reply</strong>
                  <small>
                    {threadDetail.reply_target !== null
                      ? `To ${threadDetail.reply_target}`
                      : "No reply address is available for this conversation."}
                  </small>
                </div>

                <textarea
                  aria-label="Reply message"
                  placeholder="Write a plain-text reply…"
                  value={replyBody}
                  maxLength={20000}
                  disabled={
                    replySending
                    || threadDetail.reply_target === null
                  }
                  onChange={(event) => {
                    setReplyBody(event.target.value);
                    setReplyNotice(null);
                    setReplyFailed(false);
                  }}
                />

                <div className="operations-inbox-reply-actions">
                  {replyNotice !== null ? (
                    <span
                      className={
                        replyFailed
                          ? "operations-inbox-reply-status is-error"
                          : "operations-inbox-reply-status"
                      }
                    >
                      {replyNotice}
                    </span>
                  ) : (
                    <span className="operations-inbox-reply-status">
                      Plain text · archived with this conversation
                    </span>
                  )}

                  <button
                    type="submit"
                    className="operations-action"
                    disabled={
                      replySending
                      || threadDetail.reply_target === null
                      || replyBody.trim().length === 0
                    }
                  >
                    {replySending ? "Sending…" : "Send reply"}
                  </button>
                </div>
              </form>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
