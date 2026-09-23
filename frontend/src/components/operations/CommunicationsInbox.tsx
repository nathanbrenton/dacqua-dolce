import {
  type FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getOperationsCommunicationThread,
  getOperationsCommunicationThreads,
  replyToOperationsCommunicationThread,
  updateOperationsCommunicationThreadStatus,
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
  if (message.direction === "inbound") {
    return "Received by D’Acqua Dolce";
  }

  const recipients = message.recipients
    .filter((recipient) => recipient.recipient_type === "to")
    .map((recipient) => recipient.address);

  if (recipients.length === 0) {
    return "Recipient unavailable";
  }

  return `To ${recipients.join(", ")}`;
}

type VisibleMessageBody = {
  visible: string;
  quoted: string | null;
};

function splitQuotedHistory(body: string): VisibleMessageBody {
  const markers = [
    /^On .+ wrote:\s*$/im,
    /^-{2,}\s*Original Message\s*-{2,}\s*$/im,
  ];

  let firstIndex: number | null = null;

  for (const marker of markers) {
    const match = marker.exec(body);

    if (
      match !== null
      && (
        firstIndex === null
        || match.index < firstIndex
      )
    ) {
      firstIndex = match.index;
    }
  }

  if (firstIndex === null) {
    return {
      visible: body.trim(),
      quoted: null,
    };
  }

  const visible = body.slice(0, firstIndex).trim();
  const quoted = body.slice(firstIndex).trim();

  return {
    visible,
    quoted: quoted.length > 0 ? quoted : null,
  };
}

function ArchivedMessageBody({
  message,
}: {
  message: OperationsCommunicationMessage;
}) {
  if (message.content_redacted) {
    return (
      <em>
        Sensitive message content is redacted from the archive.
      </em>
    );
  }

  if (
    message.body_text === null
    || message.body_text.trim().length === 0
  ) {
    return <em>No plain-text body archived.</em>;
  }

  const body = splitQuotedHistory(message.body_text);

  return (
    <>
      <p>{body.visible}</p>
      {body.quoted !== null ? (
        <details className="operations-inbox-quoted-history">
          <summary>Show quoted history</summary>
          <p>{body.quoted}</p>
        </details>
      ) : null}
    </>
  );
}

const AUTO_REFRESH_MS = 60_000;

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

type InboxView = "active" | "archived" | "all";

export function CommunicationsInbox() {
  const [threads, setThreads] =
    useState<OperationsCommunicationThread[]>([]);
  const [selectedThreadId, setSelectedThreadId] =
    useState<string | null>(null);
  const [threadDetail, setThreadDetail] =
    useState<OperationsCommunicationThreadDetail | null>(null);
  const [search, setSearch] = useState("");
  const [view, setView] = useState<InboxView>("active");
  const [replyBody, setReplyBody] = useState("");
  const [replyNotice, setReplyNotice] = useState<string | null>(null);
  const [replyFailed, setReplyFailed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [archivingThreadId, setArchivingThreadId] =
    useState<string | null>(null);
  const [selectionPulseThreadId, setSelectionPulseThreadId] =
    useState<string | null>(null);
  const [lastRefreshedAt, setLastRefreshedAt] =
    useState<Date | null>(null);
  const [replySending, setReplySending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    void getOperationsCommunicationThreads()
      .then((result) => {
        if (!cancelled) {
          setThreads(result);
          setLastRefreshedAt(new Date());
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

  const refreshInbox = useCallback(
    async (): Promise<void> => {
      setRefreshing(true);

      try {
        const nextThreads =
          await getOperationsCommunicationThreads();

        setThreads(nextThreads);

        if (selectedThreadId !== null) {
          const nextDetail =
            await getOperationsCommunicationThread(
              selectedThreadId,
            );
          setThreadDetail(nextDetail);
        }

        setLastRefreshedAt(new Date());
        setError(null);
      } catch (caught) {
        setError(
          caught instanceof Error
            ? caught.message
            : "Communication inbox could not be refreshed.",
        );
      } finally {
        setRefreshing(false);
      }
    },
    [selectedThreadId],
  );

  useEffect(() => {
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") {
        void refreshInbox();
      }
    }, AUTO_REFRESH_MS);

    return () => {
      window.clearInterval(timer);
    };
  }, [refreshInbox]);

  useEffect(() => {
    if (selectionPulseThreadId === null) {
      return;
    }

    const timer = window.setTimeout(() => {
      setSelectionPulseThreadId(null);
    }, 420);

    return () => {
      window.clearTimeout(timer);
    };
  }, [selectionPulseThreadId]);

  const filteredThreads = useMemo(() => {
    const query = search.trim().toLowerCase();

    return threads.filter((thread) => {
      const matchesView =
        view === "all"
        || (view === "active" && thread.status === "open")
        || (view === "archived" && thread.status === "closed");

      if (!matchesView) {
        return false;
      }

      return (
        query.length === 0
        || threadSearchText(thread).includes(query)
      );
    });
  }, [search, threads, view]);

  const inboxCounts = useMemo(() => ({
    active: threads.filter((thread) => thread.status === "open").length,
    archived: threads.filter((thread) => thread.status === "closed").length,
    all: threads.length,
  }), [threads]);

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

  async function archiveThreadFromList(
    threadId: string,
  ): Promise<void> {
    const currentIndex = filteredThreads.findIndex(
      (thread) => thread.id === threadId,
    );
    const nextThread =
      filteredThreads[currentIndex + 1]
      ?? filteredThreads[currentIndex - 1]
      ?? null;

    setRefreshing(true);
    setArchivingThreadId(threadId);
    setError(null);

    try {
      const [updated] = await Promise.all([
        updateOperationsCommunicationThreadStatus(
          threadId,
          "closed",
        ),
        new Promise<void>((resolve) => {
          window.setTimeout(resolve, 180);
        }),
      ]);

      setThreads((current) =>
        current.map((thread) =>
          thread.id === updated.id ? updated : thread,
        ),
      );
      setReplyBody("");
      setReplyNotice(null);
      setReplyFailed(false);

      if (nextThread === null) {
        setSelectedThreadId(null);
        setThreadDetail(null);
      } else {
        setSelectionPulseThreadId(nextThread.id);
        await openThread(nextThread.id);
      }
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Conversation could not be archived.",
      );
    } finally {
      setArchivingThreadId(null);
      setRefreshing(false);
    }
  }

  async function setThreadArchived(
    archived: boolean,
  ): Promise<void> {
    if (threadDetail === null) {
      return;
    }

    setRefreshing(true);
    setError(null);

    try {
      const updated =
        await updateOperationsCommunicationThreadStatus(
          threadDetail.id,
          archived ? "closed" : "open",
        );

      setThreads((current) =>
        current.map((thread) =>
          thread.id === updated.id ? updated : thread,
        ),
      );
      setThreadDetail((current) =>
        current === null
          ? null
          : {
              ...current,
              status: updated.status,
              failed_message_count: updated.failed_message_count,
            },
      );
      setReplyNotice(
        archived
          ? "Conversation archived."
          : "Conversation restored to the active inbox.",
      );
      setReplyFailed(false);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Conversation status could not be updated.",
      );
    } finally {
      setRefreshing(false);
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
      <div className="operations-inbox-heading">
        <div className="operations-section-heading">
          <p className="eyebrow">Customer Communications</p>
          <h2>Customer inbox</h2>
          <p>
            Search the durable customer email archive, inspect a
            conversation, and reply from the same thread.
          </p>
        </div>

        <div className="operations-inbox-refresh">
          <button
            type="button"
            className="operations-action secondary"
            disabled={refreshing}
            onClick={() => {
              void refreshInbox();
            }}
          >
            {refreshing ? "Refreshing…" : "Refresh"}
          </button>
          <small>
            {lastRefreshedAt === null
              ? "Auto-refreshes every 60 seconds"
              : `Updated ${lastRefreshedAt.toLocaleTimeString()} · auto-refresh 60s`}
          </small>
        </div>
      </div>

      <div
        className="operations-inbox-tabs"
        role="group"
        aria-label="Conversation view"
      >
        {(["active", "archived", "all"] as InboxView[]).map(
          (option) => (
            <button
              key={option}
              type="button"
              className={view === option ? "is-active" : ""}
              aria-pressed={view === option}
              onClick={() => {
                setView(option);
              }}
            >
              {option === "active"
                ? "Inbox"
                : option === "archived"
                  ? "Archived"
                  : "All"}
              {" "}
              <span>{inboxCounts[option]}</span>
            </button>
          ),
        )}
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
              No customer conversations yet.
            </p>
          ) : filteredThreads.length === 0 ? (
            <p className="account-muted">
              No conversations match this view.
            </p>
          ) : (
            filteredThreads.map((thread) => (
              <div
                key={thread.id}
                className={
                  "operations-inbox-thread-row "
                  + (
                    archivingThreadId === thread.id
                      ? "is-archiving"
                      : ""
                  )
                }
              >
                <button
                  type="button"
                  className={
                    "operations-inbox-thread "
                    + (
                      selectedThreadId === thread.id
                        ? "is-selected "
                        : ""
                    )
                    + (
                      selectionPulseThreadId === thread.id
                        ? "is-selection-arrival "
                        : ""
                    )
                    + (
                      thread.failed_message_count > 0
                        ? "has-failure"
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
                    {thread.status === "closed" ? "archived" : "open"}
                    {" · "}
                    {thread.message_count}
                    {thread.message_count === 1 ? " message" : " messages"}
                    {thread.failed_message_count > 0 ? (
                      <span className="operations-status-badge is-failed">
                        Failed
                      </span>
                    ) : null}
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

                {view === "active" && thread.status === "open" ? (
                  <button
                    type="button"
                    className="operations-inbox-thread-archive"
                    disabled={refreshing}
                    aria-busy={archivingThreadId === thread.id}
                    aria-label={`Archive ${
                      thread.latest_subject
                      ?? thread.subject
                      ?? "conversation"
                    }`}
                    onClick={() => {
                      void archiveThreadFromList(thread.id);
                    }}
                  >
                    Archive
                  </button>
                ) : null}
              </div>
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
                <div className="operations-inbox-conversation-titlebar">
                  <p className="product-meta">
                    {threadDetail.status === "closed" ? "archived" : "open"}
                    {" · "}
                    {threadDetail.messages.length}
                    {threadDetail.messages.length === 1
                      ? " message"
                      : " messages"}
                    {threadDetail.failed_message_count > 0 ? (
                      <span className="operations-status-badge is-failed">
                        Failed delivery
                      </span>
                    ) : null}
                  </p>
                  <button
                    type="button"
                    className="operations-action secondary compact"
                    disabled={refreshing}
                    onClick={() => {
                      void setThreadArchived(threadDetail.status !== "closed");
                    }}
                  >
                    {threadDetail.status === "closed"
                      ? "Restore to inbox"
                      : "Archive"}
                  </button>
                </div>
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
                      + `is-${message.direction} `
                      + (message.status === "failed" ? "has-failure" : "")
                    }
                  >
                    <header>
                      <div>
                        <div className="operations-inbox-message-badges">
                          <span
                            className={
                              "operations-inbox-direction "
                              + `is-${message.direction}`
                            }
                          >
                            {message.direction}
                          </span>
                          {message.status === "failed" ? (
                            <span className="operations-status-badge is-failed">
                              Failed
                            </span>
                          ) : null}
                        </div>
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
                      {recipientLabel(message)}
                    </p>

                    <h4>{message.subject}</h4>

                    <div className="operations-inbox-body">
                      <ArchivedMessageBody message={message} />
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
                    {threadDetail.status === "closed"
                      ? "Restore this conversation to the inbox before replying."
                      : threadDetail.reply_target !== null
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
                    || threadDetail.status === "closed"
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
                      || threadDetail.status === "closed"
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
