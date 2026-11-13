// Shared pieces of a customer email conversation: the archived message list
// and the reply form. Used by the Inbox and inside each request.
import {
  Fragment,
  type FormEvent,
  type ReactNode,
  useEffect,
  useState,
} from "react";

import type { OperationsCommunicationMessage } from "../../api/operations";

export function formatTimestamp(value: string | null): string {
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

function replyTargetSourceLabel(value: string | null): string | null {
  switch (value) {
    case "latest_inbound_sender":
      return "Latest customer message";
    case "quote_request":
      return "Quote request";
    case "account_email":
      return "Account email";
    case "latest_outbound_recipient":
      return "Previous outbound message";
    default:
      return null;
  }
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

const HTTP_URL_PATTERN = /https?:\/\/[^\s<>"']+/gi;
const INBOUND_URL_PATTERN = /https?:\/\//i;
const SIMPLE_TRAILING_URL_PUNCTUATION = /[.,!?;:]+$/;

function splitTrailingUrlPunctuation(value: string): {
  href: string;
  trailing: string;
} {
  let href = value;
  let trailing = "";

  const simple = SIMPLE_TRAILING_URL_PUNCTUATION.exec(href);
  if (simple !== null) {
    trailing = simple[0] + trailing;
    href = href.slice(0, -simple[0].length);
  }

  const pairedDelimiters: Array<[string, string]> = [
    ["(", ")"],
    ["[", "]"],
    ["{", "}"],
  ];

  for (const [opening, closing] of pairedDelimiters) {
    while (href.endsWith(closing)) {
      const openingCount = href.split(opening).length - 1;
      const closingCount = href.split(closing).length - 1;

      if (closingCount <= openingCount) {
        break;
      }

      trailing = closing + trailing;
      href = href.slice(0, -1);
    }
  }

  return { href, trailing };
}

function PlainTextWithLinks({ text }: { text: string }) {
  const nodes: ReactNode[] = [];
  let cursor = 0;
  let part = 0;

  for (const match of text.matchAll(HTTP_URL_PATTERN)) {
    const raw = match[0];
    const index = match.index ?? cursor;

    if (index > cursor) {
      nodes.push(
        <Fragment key={`text-${part}`}>
          {text.slice(cursor, index)}
        </Fragment>,
      );
      part += 1;
    }

    const { href, trailing } = splitTrailingUrlPunctuation(raw);
    let isSafeHttpUrl = false;

    try {
      const parsed = new URL(href);
      isSafeHttpUrl =
        parsed.protocol === "http:" || parsed.protocol === "https:";
    } catch {
      isSafeHttpUrl = false;
    }

    if (isSafeHttpUrl) {
      nodes.push(
        <a
          key={`link-${part}`}
          href={href}
          target="_blank"
          rel="noopener noreferrer"
        >
          {href}
        </a>,
      );
      part += 1;

      if (trailing.length > 0) {
        nodes.push(
          <Fragment key={`trailing-${part}`}>
            {trailing}
          </Fragment>,
        );
        part += 1;
      }
    } else {
      nodes.push(
        <Fragment key={`url-text-${part}`}>{raw}</Fragment>,
      );
      part += 1;
    }

    cursor = index + raw.length;
  }

  if (cursor < text.length) {
    nodes.push(
      <Fragment key={`text-${part}`}>{text.slice(cursor)}</Fragment>,
    );
  }

  return <>{nodes}</>;
}

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


function messageSourceLabel(
  message: OperationsCommunicationMessage,
): string {
  if (message.provider === "web") {
    return "Website";
  }

  if (message.provider === "postmark") {
    return "Email";
  }

  return "Archived";
}

function MessageSecuritySummary({
  message,
}: {
  message: OperationsCommunicationMessage;
}) {
  if (
    message.direction !== "inbound"
    || message.security == null
  ) {
    return null;
  }

  const security = message.security;
  const spamStatus =
    security.spam_status?.toLowerCase() ?? null;
  const spfResult =
    security.spf_result?.toLowerCase() ?? null;
  const spamWarning = spamStatus === "yes";
  const spfWarning =
    spfResult === "fail"
    || spfResult === "softfail"
    || spfResult === "permerror";

  return (
    <div className="operations-inbox-message-badges">
      {spamStatus !== null
        || security.spam_score !== null ? (
        <span
          className={
            "operations-status-badge"
            + (spamWarning ? " is-failed" : "")
          }
          title={
            security.spam_tests.length > 0
              ? `Spam checks: ${security.spam_tests.join(", ")}`
              : "Postmark spam assessment"
          }
        >
          Spam: {spamStatus ?? "unknown"}
          {security.spam_score !== null
            ? ` · score ${security.spam_score}`
            : ""}
        </span>
      ) : null}
      {spfResult !== null ? (
        <span
          className={
            "operations-status-badge"
            + (spfWarning ? " is-failed" : "")
          }
        >
          SPF: {spfResult}
        </span>
      ) : null}
    </div>
  );
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
  const inbound = message.direction === "inbound";
  const hasInboundUrl =
    inbound && INBOUND_URL_PATTERN.test(message.body_text);

  return (
    <>
      <p>
        {inbound
          ? body.visible
          : <PlainTextWithLinks text={body.visible} />}
      </p>
      {hasInboundUrl ? (
        <small>
          Inbound URLs are shown as plain text to reduce accidental phishing clicks.
        </small>
      ) : null}
      {body.quoted !== null ? (
        <details className="operations-inbox-quoted-history">
          <summary>Show quoted history</summary>
          <p>
            {inbound
              ? body.quoted
              : <PlainTextWithLinks text={body.quoted} />}
          </p>
        </details>
      ) : null}
    </>
  );
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

/** The archived messages of one conversation, oldest first. */
export function ConversationMessageList({
  messages,
  label = "Conversation history",
}: {
  messages: OperationsCommunicationMessage[];
  // null hides the label (e.g. when the surrounding section already names it).
  label?: string | null;
}) {
  return (
    <div className="operations-inbox-message-list">
      {label !== null ? (
        <p className="operations-inbox-message-list-label">{label}</p>
      ) : null}
      {messages.map((message) => (
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
                <span className="operations-status-badge">
                  {messageSourceLabel(message)}
                </span>
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

          <MessageSecuritySummary message={message} />

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
  );
}

export type ConversationReplyOutcome = {
  delivery_status: string;
  sender: string;
};

type ConversationReplyFormProps = {
  heading?: string;
  senderAddresses: string[];
  defaultSender: string | null;
  defaultRecipient: string | null;
  recipientSource: string | null;
  // Shown as a hint when it differs from the suggested recipient.
  accountEmail?: string | null;
  // Archived conversations can't be replied to until restored.
  closedHint?: string | null;
  // A notice from outside the form (e.g. "Conversation archived."). Each new
  // value replaces whatever the form was showing.
  statusNotice?: string | null;
  onSubmit: (
    body: string,
    recipient: string,
    sender: string,
  ) => Promise<ConversationReplyOutcome>;
};

/**
 * Plain-text reply box with sender and recipient. It keeps its own draft, so
 * give it a `key` per conversation to start each one fresh.
 */
export function ConversationReplyForm({
  heading = "Reply",
  senderAddresses,
  defaultSender,
  defaultRecipient,
  recipientSource,
  accountEmail = null,
  closedHint = null,
  statusNotice = null,
  onSubmit,
}: ConversationReplyFormProps) {
  const [body, setBody] = useState("");
  const [recipient, setRecipient] = useState(defaultRecipient ?? "");
  const [sender, setSender] = useState(defaultSender ?? "");
  const [notice, setNotice] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    setNotice(statusNotice);
    setFailed(false);
  }, [statusNotice]);

  const closed = closedHint !== null;

  function clearNotice(): void {
    setNotice(null);
    setFailed(false);
  }

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    if (
      closed
      || body.trim().length === 0
      || recipient.trim().length === 0
      || sender.trim().length === 0
    ) {
      return;
    }

    setSending(true);
    clearNotice();

    try {
      const result = await onSubmit(body, recipient, sender);

      setSender(result.sender);
      setNotice(deliveryNotice(result.delivery_status));
      setFailed(result.delivery_status === "failed");

      if (result.delivery_status !== "failed") {
        setBody("");
      }
    } catch (caught) {
      setFailed(true);
      setNotice(
        caught instanceof Error
          ? caught.message
          : "Reply could not be submitted.",
      );
    } finally {
      setSending(false);
    }
  }

  return (
    <form
      className="operations-inbox-reply"
      onSubmit={(event) => {
        void submit(event);
      }}
    >
      <div>
        <strong>{heading}</strong>
        <small>{closedHint ?? "Confirm the recipient before sending."}</small>
      </div>

      <label className="operations-inbox-reply-recipient-field">
        <span>From</span>
        <select
          aria-label="Reply sender"
          value={sender}
          required
          disabled={sending || closed || senderAddresses.length === 0}
          onChange={(event) => {
            setSender(event.target.value);
            clearNotice();
          }}
        >
          {senderAddresses.map((address) => (
            <option key={address} value={address}>
              {address}
            </option>
          ))}
        </select>
        <small>
          Approved D’Acqua Dolce sender · customer replies remain
          attached to this archived conversation.
        </small>
      </label>

      <label className="operations-inbox-reply-recipient-field">
        <span>To</span>
        <input
          type="text"
          inputMode="email"
          aria-label="Reply recipients"
          placeholder="customer@example.com"
          value={recipient}
          maxLength={320}
          required
          disabled={sending || closed}
          onChange={(event) => {
            setRecipient(event.target.value);
            clearNotice();
          }}
        />
        <small>
          {defaultRecipient !== null
            ? `Suggested from: ${replyTargetSourceLabel(recipientSource) ?? "conversation"}`
            : "No suggested address is available. Enter a recipient."}
          {accountEmail !== null && accountEmail !== defaultRecipient
            ? ` · Account email: ${accountEmail}`
            : ""}
          {" · Separate multiple recipients with commas or semicolons."}
        </small>
      </label>

      <textarea
        aria-label="Reply message"
        placeholder="Write a plain-text reply…"
        value={body}
        maxLength={20000}
        disabled={sending || closed}
        onChange={(event) => {
          setBody(event.target.value);
          clearNotice();
        }}
      />

      <div className="operations-inbox-reply-actions">
        <span
          className={
            failed
              ? "operations-inbox-reply-status is-error"
              : "operations-inbox-reply-status"
          }
        >
          {notice ?? "Plain text · archived with this conversation"}
        </span>

        <button
          type="submit"
          className="operations-action"
          disabled={
            sending
            || closed
            || recipient.trim().length === 0
            || sender.trim().length === 0
            || body.trim().length === 0
          }
        >
          {sending ? "Sending…" : "Send reply"}
        </button>
      </div>
    </form>
  );
}
