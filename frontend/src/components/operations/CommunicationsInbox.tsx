import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  getOperationsCommunicationThread,
  getOperationsCommunicationThreads,
  replyToOperationsCommunicationThread,
  updateOperationsCommunicationThreadStatus,
  type OperationsCommunicationThread,
  type OperationsCommunicationThreadDetail,
} from "../../api/operations";
import {
  ConversationMessageList,
  ConversationReplyForm,
  formatTimestamp,
} from "./ConversationThread";

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



const AUTO_REFRESH_MS = 60_000;

function relatedRecordLabel(
  type: string | null,
  originatingRequestType: string | null,
): string | null {
  if (type === null) {
    return null;
  }

  // Only persisted originating-request provenance determines inquiry badges.
  // Do not infer classification from subject lines or message content.
  if (type === "quote_request") {
    switch (originatingRequestType) {
      case "website_expert_inquiry":
        return "Expert inquiry";
      case "website_product_inquiry":
        return "Product inquiry";
      case "website_recommendation_inquiry":
        return "Recommendation inquiry";
      default:
        return "Quote request";
    }
  }

  const labels: Record<string, string> = {
    user: "Customer account",
    order: "Customer order",
  };

  return labels[type] ?? "Related record";
}


type InboxView = "active" | "system" | "archived" | "all";

type CommunicationsInboxProps = {
  // Reports how many open customer conversations sit in the Inbox view, so
  // the Operations navigation can show the count next to the Inbox tab.
  onActiveCountChange?: (count: number) => void;
  // Reports open Inbox conversations whose latest message is the customer's,
  // for the Overview's "Needs you" list.
  onAwaitingReplyChange?: (threads: OperationsCommunicationThread[]) => void;
  // Shows an "Open request" link on conversations linked to a request.
  onOpenRequest?: (quoteId: string) => void;
  // Opens this conversation (from a request's "Open in Inbox"). A new object
  // reopens it even when the thread id is unchanged.
  threadToOpen?: { threadId: string } | null;
};

export function CommunicationsInbox({
  onActiveCountChange,
  onAwaitingReplyChange,
  onOpenRequest,
  threadToOpen = null,
}: CommunicationsInboxProps = {}) {
  const [threads, setThreads] =
    useState<OperationsCommunicationThread[]>([]);
  const [selectedThreadId, setSelectedThreadId] =
    useState<string | null>(null);
  const [threadDetail, setThreadDetail] =
    useState<OperationsCommunicationThreadDetail | null>(null);
  const [search, setSearch] = useState("");
  const [view, setView] = useState<InboxView>("active");
  // Archive/restore notices shown in the reply form's status line.
  const [statusNotice, setStatusNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [archivingThreadId, setArchivingThreadId] =
    useState<string | null>(null);
  const [selectionPulseThreadId, setSelectionPulseThreadId] =
    useState<string | null>(null);
  const searchInputRef =
    useRef<HTMLInputElement>(null);
  const threadButtonRefs =
    useRef<Map<string, HTMLButtonElement>>(new Map());
  const [lastRefreshedAt, setLastRefreshedAt] =
    useState<Date | null>(null);
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
        || (
          view === "active"
          && thread.status === "open"
          && thread.mailbox_kind === "inbox"
        )
        || (view === "system" && thread.mailbox_kind === "system")
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
    active: threads.filter(
      (thread) => thread.status === "open" && thread.mailbox_kind === "inbox",
    ).length,
    system: threads.filter((thread) => thread.mailbox_kind === "system").length,
    archived: threads.filter((thread) => thread.status === "closed").length,
    all: threads.length,
  }), [threads]);

  useEffect(() => {
    onActiveCountChange?.(inboxCounts.active);
  }, [inboxCounts.active, onActiveCountChange]);

  const awaitingReplyThreads = useMemo(
    () => threads.filter(
      (thread) =>
        thread.status === "open"
        && thread.mailbox_kind === "inbox"
        && thread.latest_direction === "inbound",
    ),
    [threads],
  );

  useEffect(() => {
    onAwaitingReplyChange?.(awaitingReplyThreads);
  }, [awaitingReplyThreads, onAwaitingReplyChange]);

  async function openThread(threadId: string): Promise<void> {
    setSelectedThreadId(threadId);
    setDetailLoading(true);
    setStatusNotice(null);
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

  useEffect(() => {
    if (threadToOpen === null) {
      return;
    }

    const { threadId } = threadToOpen;
    setSearch("");
    void openThread(threadId);

    // Refresh the list (the thread may be new or just replied to), then pick
    // a view that shows it: archived or system threads aren't in "Inbox".
    void getOperationsCommunicationThreads()
      .then((nextThreads) => {
        setThreads(nextThreads);
        setLastRefreshedAt(new Date());
        const listed = nextThreads.find((thread) => thread.id === threadId);
        if (listed !== undefined) {
          setView(
            listed.status === "open" && listed.mailbox_kind === "inbox"
              ? "active"
              : "all",
          );
        }
      })
      .catch(() => {
        // The conversation itself still opens; the list catches up on the
        // next refresh.
      });
    // Only a new request to open should trigger this, not list refreshes.
  }, [threadToOpen]);

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
      setStatusNotice(null);

      if (nextThread === null) {
        setSelectedThreadId(null);
        setThreadDetail(null);

        window.requestAnimationFrame(() => {
          searchInputRef.current?.focus();
        });
      } else {
        setSelectionPulseThreadId(nextThread.id);
        const openNextThread = openThread(nextThread.id);

        window.requestAnimationFrame(() => {
          threadButtonRefs.current
            .get(nextThread.id)
            ?.focus();
        });

        await openNextThread;
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
      setStatusNotice(
        archived
          ? "Conversation archived."
          : "Conversation restored to the active inbox.",
      );
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

  async function sendReply(
    threadId: string,
    body: string,
    recipient: string,
    sender: string,
  ): Promise<{ delivery_status: string; sender: string }> {
    const result = await replyToOperationsCommunicationThread(
      threadId,
      body,
      recipient,
      sender,
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

    return result;
  }

  return (
    <div className="operations-inbox">
      <div className="operations-inbox-heading">
        <div className="operations-section-heading">
          <p className="eyebrow">Customer Communications</p>
          <h2>Customer inbox</h2>
          <p>
            Search the durable customer communications archive, inspect a
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
        {(["active", "system", "archived", "all"] as InboxView[]).map(
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
                : option === "system"
                  ? "System"
                  : option === "archived"
                    ? "Archived"
                    : "All"}
              {" "}
              <span>{inboxCounts[option]}</span>
            </button>
          ),
        )}
      </div>

      <p className="operations-inbox-filter-note">
        {view === "active"
          ? "Customer correspondence requiring normal attention."
          : view === "system"
            ? "Account verification, password reset, welcome, and other application-generated messages."
            : view === "archived"
              ? "Conversations deliberately archived by an employee."
              : "Complete authoritative communications archive."}
      </p>

      <label
        className="operations-field operations-customer-search"
      >
        <span>Search conversations</span>
        <input
          ref={searchInputRef}
          type="search"
          placeholder="Customer, sender, subject, status, related record…"
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
          }}
        />
      </label>

      {error !== null ? (
        <p
          className="operations-alert operations-error"
          role="alert"
        >
          {error}
        </p>
      ) : null}

      <div className="operations-inbox-layout">
        <div
          className="operations-inbox-thread-list"
          aria-label="Communication threads"
          aria-busy={loading || refreshing}
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
                  ref={(element) => {
                    if (element === null) {
                      threadButtonRefs.current.delete(thread.id);
                      return;
                    }

                    threadButtonRefs.current.set(thread.id, element);
                  }}
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
                  threadDetail.originating_request?.request_type ?? null,
                ) !== null ? (
                  <div className="operations-inbox-related-row">
                    <small className="operations-inbox-related">
                      {relatedRecordLabel(
                        threadDetail.related_entity_type,
                        threadDetail.originating_request?.request_type ?? null,
                      )}
                    </small>
                    {threadDetail.related_entity_type === "quote_request"
                      && threadDetail.related_entity_id !== null
                      && onOpenRequest !== undefined ? (
                        <button
                          type="button"
                          className="operations-inbox-open-request"
                          onClick={() => {
                            onOpenRequest(threadDetail.related_entity_id as string);
                          }}
                        >
                          Open request →
                        </button>
                      ) : null}
                  </div>
                ) : null}
              </header>

              {threadDetail.originating_request !== null ? (
                <article className="operations-inbox-originating-request">
                  <header>
                    <div>
                      <span className="operations-inbox-direction">
                        {threadDetail.originating_request.request_type.includes("support_request")
                          ? "Original support request"
                          : "Original website request"}
                      </span>
                      <strong>
                        {threadDetail.originating_request.name}
                      </strong>
                    </div>
                    <small>
                      {formatTimestamp(
                        threadDetail.originating_request.created_at,
                      )}
                    </small>
                  </header>

                  <p className="operations-inbox-originating-request-contact">
                    {threadDetail.originating_request.email}
                    {threadDetail.originating_request.phone !== null
                      ? ` · ${threadDetail.originating_request.phone}`
                      : ""}
                  </p>

                  <h4>
                    {threadDetail.originating_request.product_name
                      ?? (threadDetail.originating_request.request_type.includes("support_request")
                        ? "General support"
                        : "General consultation")}
                  </h4>

                  <div className="operations-inbox-body">
                    {threadDetail.originating_request.message !== null
                      && threadDetail.originating_request.message.trim().length > 0 ? (
                        <p>
                          {threadDetail.originating_request.message}
                        </p>
                      ) : (
                        <em>No written question was included with this request.</em>
                      )}
                  </div>
                </article>
              ) : null}

              <ConversationMessageList messages={threadDetail.messages} />

              <ConversationReplyForm
                key={threadDetail.id}
                senderAddresses={threadDetail.reply_sender_addresses}
                defaultSender={threadDetail.reply_sender_default}
                defaultRecipient={threadDetail.reply_target}
                recipientSource={threadDetail.reply_target_source}
                accountEmail={threadDetail.customer_email}
                closedHint={
                  threadDetail.status === "closed"
                    ? "Restore this conversation to the inbox before replying."
                    : null
                }
                statusNotice={statusNotice}
                onSubmit={(body, recipient, sender) =>
                  sendReply(threadDetail.id, body, recipient, sender)}
              />
            </>
          )}
        </section>
      </div>
    </div>
  );
}
