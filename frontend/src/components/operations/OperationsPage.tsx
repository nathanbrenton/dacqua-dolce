import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getProfile,
  type CustomerProfile,
} from "../../api/account";
import { homeSizeLabel } from "../../api/quotes";
import { contactMethodLabel } from "../../utils/contactMethod";
import { splitRequestMessage } from "./operationsMoney";

import {
  getOperationsCommunications,
  reviewOperationsCommunications,
  getOperationsCatalog,
  getOperationsCustomers,
  getOperationsLaunchReadiness,
  getOperationsOrders,
  getOperationsQuotes,
  getOperationsSalesInsights,
  getOperationsSummary,
  updateQuoteNotes,
  updateQuoteStatus,
  type OperationsCommunication,
  type OperationsCommunicationThread,
  type OperationsCommunicationThreadDetail,
  type OperationsCustomer,
  type OperationsOrder,
  type OperationsFormalQuote,
  type OperationsLaunchReadiness,
  type OperationsProduct,
  type OperationsQuote,
  type OperationsSalesInsights,
  type OperationsSummary,
} from "../../api/operations";

import {
  BrandLogo,
} from "../brand/BrandLogo";
import {
  DeveloperFooterLogo,
} from "../brand/DeveloperFooterLogo";
import { formatRequestAge } from "./formatRequestAge";
import { NeedsYouList } from "./NeedsYouList";
import { RequestConversation } from "./RequestConversation";
import { RequestWorkflowProgress } from "./RequestWorkflowProgress";
import {
  FooterCopyright,
} from "../brand/FooterCopyright";
import { CopyEmailButton } from "./CopyEmailButton";
import { type SaveState } from "./operationsShared";
import { AuditWorkspace } from "./workspaces/AuditWorkspace";
import { CatalogWorkspace } from "./workspaces/CatalogWorkspace";
import { CustomersWorkspace } from "./workspaces/CustomersWorkspace";
import { InstallersWorkspace } from "./workspaces/InstallersWorkspace";
import { OrdersWorkspace } from "./workspaces/OrdersWorkspace";
import { StaffWorkspace } from "./workspaces/StaffWorkspace";

import {
  CommunicationsInbox,
} from "./CommunicationsInbox";
import {
  FormalQuoteComposer,
} from "./FormalQuoteComposer";
import {
  LaunchDependencyEvidencePanel,
} from "./LaunchDependencyEvidencePanel";
import {
  PolicyManagementPanel,
} from "./PolicyManagementPanel";

import {
  type AppearanceMode,
} from "../../theme/appearance";
import {
  type LogoVariantId,
} from "../../theme/branding";

import {
  formatUsPhoneInput,
} from "../../utils/phone";

type OperationsPageProps = {
  roles: string[];
  currentUserEmail: string | null;
  onNavigate: (path: string) => void;
  appearance: AppearanceMode;
  logoVariant: LogoVariantId;
  developerControlsOpen: boolean;
  onToggleDeveloperControls: () => void;
};

type OperationsWorkspace =
  | "overview"
  | "requests"
  | "orders"
  | "catalog"
  | "customers"
  | "communications"
  | "installers"
  | "staff"
  | "audit";

type OperationsWorkspaceGroup = "daily" | "store" | "admin";

// Tabs are grouped by how often they're used: day-to-day customer work first,
// then store records, then administration.
const OPERATIONS_WORKSPACE_GROUPS: ReadonlyArray<{
  id: OperationsWorkspaceGroup;
  label: string;
}> = [
  { id: "daily", label: "Daily" },
  { id: "store", label: "Store" },
  { id: "admin", label: "Admin" },
];

const OPERATIONS_WORKSPACES: ReadonlyArray<{
  id: OperationsWorkspace;
  label: string;
  description: string;
  group: OperationsWorkspaceGroup;
}> = [
  { id: "overview", label: "Overview", description: "Priorities & readiness", group: "daily" },
  { id: "communications", label: "Inbox", description: "Inbox & delivery", group: "daily" },
  { id: "requests", label: "Requests", description: "Quotes & triage", group: "daily" },
  { id: "orders", label: "Orders", description: "Fulfillment", group: "daily" },
  { id: "catalog", label: "Catalog", description: "Pricing & inventory", group: "store" },
  { id: "customers", label: "Customers", description: "Accounts & equipment", group: "store" },
  { id: "installers", label: "Installers", description: "Internal research", group: "store" },
  { id: "staff", label: "Staff", description: "User access & roles", group: "admin" },
  { id: "audit", label: "Audit", description: "Activity & troubleshooting", group: "admin" },
];

const OPERATIONS_TARGET_WORKSPACES: Record<string, OperationsWorkspace> = {
  "launch-readiness": "overview",
  "assisted-sales-insights": "overview",
  "launch-policies": "overview",
  "email-delivery-issues": "communications",
  "communications-history": "communications",
  "quote-queue": "requests",
  "order-history": "orders",
  "catalog-governance": "catalog",
  "customer-roster": "customers",
  "installer-candidates": "installers",
  "account-administration": "staff",
  "audit-events": "audit",
};

const OPERATIONS_ROLES = new Set([
  "employee",
  "manager",
  "administrator",
  "developer",
]);

const WRITE_ROLES = new Set([
  "administrator",
  "developer",
]);


const AUDIT_LOG_ROLES = new Set([
  "developer",
]);

const ADMINISTRATION_ROLES = new Set([
  "administrator",
  "developer",
]);

const QUOTE_STATUSES = [
  "new",
  "contacted",
  "quoted",
  "closed",
] as const;

const QUOTE_STATUS_LABELS: Record<
  (typeof QUOTE_STATUSES)[number],
  string
> = {
  new: "New",
  contacted: "Contacted",
  quoted: "Quoted",
  closed: "Closed",
};

type QuoteStatus = (typeof QUOTE_STATUSES)[number];

// Compact age for the request queue: "Just now", "45m", "3h", "2d", or a date.
const RECOMMENDATION_COMPONENT_LABELS: Record<string, string> = {
  harmony: "Harmony",
  cartridge_filtration: "Cartridge filtration",
  backwashing_carbon: "Backwashing carbon",
  water_softener: "Water softener",
  reverse_osmosis: "Reverse osmosis",
};

function recommendationContextLabel(key: string): string {
  return key
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function recommendationContextValue(key: string, value: unknown): string {
  if (key === "home_size" && typeof value === "string") {
    const label = homeSizeLabel(value);
    if (label !== null) {
      return label;
    }
  }

  if (value === "yes") {
    return "Yes";
  }

  if (value === "no") {
    return "No";
  }

  if (value === "unsure") {
    return "Not sure";
  }

  if (value === null || value === undefined || value === "") {
    return "—";
  }

  return String(value).replaceAll("_", " ");
}

type RequestView = "active" | "closed" | "all";
type RecommendationTriageView =
  | "all"
  | "guided"
  | "human_review"
  | "lab_testing";

function replaceProduct(
  products: OperationsProduct[],
  replacement: OperationsProduct,
): OperationsProduct[] {
  return products.map((product) =>
    product.id === replacement.id ? replacement : product,
  );
}

export function OperationsPage({
  roles,
  currentUserEmail,
  onNavigate,
  appearance,
  logoVariant,
  developerControlsOpen,
  onToggleDeveloperControls,
}: OperationsPageProps) {
  const authorized = useMemo(
    () => roles.some((role) => OPERATIONS_ROLES.has(role)),
    [roles],
  );

  const privileged = useMemo(
    () => roles.some((role) => WRITE_ROLES.has(role)),
    [roles],
  );

  const auditLogAllowed = useMemo(
    () => roles.some((role) => AUDIT_LOG_ROLES.has(role)),
    [roles],
  );

  const administrationAllowed = useMemo(
    () => roles.some((role) => ADMINISTRATION_ROLES.has(role)),
    [roles],
  );

  const [activeWorkspace, setActiveWorkspace] =
    useState<OperationsWorkspace>("overview");
  const [activeInboxCount, setActiveInboxCount] = useState(0);
  // Set by a request's "Open in Inbox"; a new object reopens the thread.
  const [inboxThreadToOpen, setInboxThreadToOpen] =
    useState<{ threadId: string } | null>(null);
  // Open Inbox conversations where the customer wrote last (for Needs you).
  // Latest thread from a reply sent inside a request, passed to the Inbox.
  const [requestReplyThread, setRequestReplyThread] =
    useState<OperationsCommunicationThreadDetail | null>(null);
  const [awaitingReplyThreads, setAwaitingReplyThreads] =
    useState<OperationsCommunicationThread[]>([]);

  const visibleWorkspaces = useMemo(() =>
    OPERATIONS_WORKSPACES.filter(({ id }) =>
      (id !== "staff" || administrationAllowed)
      && (id !== "audit" || auditLogAllowed),
    ),
    [administrationAllowed, auditLogAllowed],
  );

  useEffect(() => {
    if (
      (activeWorkspace === "staff" && !administrationAllowed)
      || (activeWorkspace === "audit" && !auditLogAllowed)
    ) {
      setActiveWorkspace("overview");
    }
  }, [activeWorkspace, administrationAllowed, auditLogAllowed]);

  // Preserve the mounted forms and drafts when navigating away. Open the
  // selected workspace's disclosure so a tab never lands on a closed row.
  useEffect(() => {
    if (activeWorkspace === "overview") {
      return;
    }
    const panel = document.getElementById(
      `operations-panel-${activeWorkspace}`,
    );
    const disclosure = panel?.querySelector("details.operations-disclosure");
    if (disclosure instanceof HTMLDetailsElement) {
      disclosure.open = true;
    }
  }, [activeWorkspace]);

  function chooseWorkspace(next: OperationsWorkspace): void {
    if (!visibleWorkspaces.some(({ id }) => id === next)) {
      return;
    }
    setActiveWorkspace(next);
    window.requestAnimationFrame(() => {
      document.getElementById("operations-primary-nav")?.scrollIntoView({
        behavior: "auto",
        block: "start",
      });
    });
  }

  const [summary, setSummary] =
    useState<OperationsSummary | null>(null);
  const [launchReadiness, setLaunchReadiness] =
    useState<OperationsLaunchReadiness | null>(null);
  const [salesInsights, setSalesInsights] =
    useState<OperationsSalesInsights | null>(null);

  // Overview's counts and readiness snapshot are worked out on the server from
  // catalog, request and policy data. Refetch them after a save elsewhere so
  // Overview and the tab badges never lag behind the change.
  const refreshOverviewData = useCallback(() => {
    void Promise.all([
      getOperationsSummary(),
      getOperationsLaunchReadiness(),
    ])
      .then(([nextSummary, nextReadiness]) => {
        setSummary(nextSummary);
        setLaunchReadiness(nextReadiness);
      })
      .catch(() => undefined);
  }, []);
  const [quotes, setQuotes] =
    useState<OperationsQuote[]>([]);
  const [requestView, setRequestView] =
    useState<RequestView>("active");
  const [recommendationTriageView, setRecommendationTriageView] =
    useState<RecommendationTriageView>("all");
  const [selectedQuoteId, setSelectedQuoteId] =
    useState<string | null>(null);
  const [communications, setCommunications] =
    useState<OperationsCommunication[]>([]);
  const [operatorProfile, setOperatorProfile] =
    useState<CustomerProfile | null>(null);
  const [customers, setCustomers] =
    useState<OperationsCustomer[]>([]);
  const [orders, setOrders] =
    useState<OperationsOrder[]>([]);
  const [orderSearch, setOrderSearch] =
    useState("");
  const [products, setProducts] =
    useState<OperationsProduct[]>([]);
  const [quoteNoteDrafts, setQuoteNoteDrafts] =
    useState<Record<string, string>>({});
  const [error, setError] =
    useState<string | null>(null);
  const [message, setMessage] =
    useState<string | null>(null);
  const [loading, setLoading] =
    useState(true);
  const [
    quoteNoteSaveStates,
    setQuoteNoteSaveStates,
  ] = useState<Record<string, SaveState>>({});

  useEffect(() => {
    if (!authorized) {
      setLoading(false);
      return;
    }

    void Promise.all([
      getOperationsSummary(),
      getOperationsLaunchReadiness(),
      getOperationsQuotes(),
      getOperationsCommunications(),
      getOperationsCustomers(),
      getOperationsOrders(),
      getOperationsCatalog(),
      getOperationsSalesInsights(),
    ])
      .then(([
        summaryResult,
        launchReadinessResult,
        quoteResult,
        communicationResult,
        customerResult,
        orderResult,
        productResult,
        salesInsightsResult,
      ]) => {
        setSummary(summaryResult);
        setLaunchReadiness(launchReadinessResult);
        setSalesInsights(salesInsightsResult);
        setQuotes(quoteResult);
        setCommunications(communicationResult);
        setCustomers(customerResult);
        setOrders(orderResult);
        setProducts(productResult);

        const nextQuoteNotes: Record<string, string> = {};

        for (const quote of quoteResult) {
          nextQuoteNotes[quote.id] =
            quote.internal_notes ?? "";
        }

        setQuoteNoteDrafts(nextQuoteNotes);
        setError(null);
      })
      .catch((caught) => {
        setError(
          caught instanceof Error
            ? caught.message
            : "Operations data could not be loaded.",
        );
      })
      .finally(() => {
        setLoading(false);
      });
  }, [authorized]);

  useEffect(() => {
    if (!authorized) {
      return;
    }

    let cancelled = false;

    void getProfile()
      .then((profile) => {
        if (!cancelled) {
          setOperatorProfile(profile);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setOperatorProfile(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [authorized]);



  // Keep every Hook above the authorization return below. On a hard
  // refresh the session starts unresolved, so roles can legitimately change
  // from [] to an authorized set between renders. Conditional Hooks here
  // would violate React's Rules of Hooks and blank the Operations route.
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
    if (recommendationTriageView === "all") {
      return lifecycleQuotes;
    }

    return lifecycleQuotes.filter((quote) => {
      if (recommendationTriageView === "guided") {
        return quote.recommendation_context !== null;
      }

      if (recommendationTriageView === "human_review") {
        return quote.recommendation_decision?.human_review === true;
      }

      return (
        quote.recommendation_decision?.requires_third_party_lab === true
      );
    });
  }, [lifecycleQuotes, recommendationTriageView]);

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

  const failedDeliveries = useMemo(
    () => communications.filter(
      (item) => item.status === "failed" && item.requires_review,
    ),
    [communications],
  );

  const [reviewingDeliveryIds, setReviewingDeliveryIds] =
    useState<string[]>([]);

  async function markDeliveriesReviewed(deliveryIds: string[]): Promise<void> {
    setReviewingDeliveryIds(deliveryIds);
    setError(null);
    try {
      const reviewed = await reviewOperationsCommunications(deliveryIds);
      const reviewedById = new Map(reviewed.map((item) => [item.id, item]));
      setCommunications((current) => current.map(
        (item) => reviewedById.get(item.id) ?? item,
      ));
      setSummary(await getOperationsSummary());
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

  if (!authorized) {
    return (
      <main
        id="main-content"
        tabIndex={-1}
        className="operations-shell"
      >
        <button
          type="button"
          className="text-button"
          onClick={() => onNavigate("/")}
        >
          ← Home
        </button>

        <section className="operations-denied">
          <p className="eyebrow">Operations</p>
          <h1>Access restricted.</h1>
          <p>
            This workspace is limited to authorized operations roles.
          </p>
        </section>
      </main>
    );
  }

  function mergeFormalQuote(
    requestId: string,
    formalQuote: OperationsFormalQuote,
  ): void {
    setQuotes((current) => current.map((quote) => {
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

      setQuotes((current) =>
        current.map((candidate) =>
          candidate.id === updated.id ? updated : candidate,
        ),
      );

      setSummary(await getOperationsSummary());
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
      quoteNoteDrafts[quote.id];

    if (draft === undefined) {
      return;
    }

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

      setQuotes((current) =>
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


  const operatorName = [
    operatorProfile?.first_name,
    operatorProfile?.last_name,
  ]
    .filter((value): value is string => (
      typeof value === "string" && value.trim().length > 0
    ))
    .join(" ");

  // Counts shown beside a nav tab when that workspace has work waiting.
  const workspaceWaitingCounts: Partial<
    Record<OperationsWorkspace, { count: number; description: string }>
  > = {
    requests: {
      count: summary?.new_quotes ?? 0,
      description: (summary?.new_quotes ?? 0) === 1 ? "new request" : "new requests",
    },
    communications: {
      count: activeInboxCount,
      description: activeInboxCount === 1 ? "open conversation" : "open conversations",
    },
  };

  function scrollToOperationsTarget(
    targetId: string,
    selector?: string,
  ) {
    const workspace = OPERATIONS_TARGET_WORKSPACES[targetId];
    if (workspace && visibleWorkspaces.some(({ id }) => id === workspace)) {
      setActiveWorkspace(workspace);
    }
    window.requestAnimationFrame(() => {
      const fallback = document.getElementById(targetId);
      const target = selector
        ? document.querySelector(selector)
        : fallback;
      const scrollTarget = target ?? fallback;

      let disclosure = scrollTarget?.closest("details") ?? null;
      while (disclosure instanceof HTMLDetailsElement) {
        disclosure.open = true;
        disclosure = disclosure.parentElement?.closest("details") ?? null;
      }

      window.requestAnimationFrame(() => {
        scrollTarget?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      });
    });
  }

  function openOperationsMetric(
    metric:
      | "new_quotes"
      | "open_quotes"
      | "human_review"
      | "lab_testing"
      | "active_products"
      | "email_failures",
  ) {
    if (metric === "active_products") {
      scrollToOperationsTarget("catalog-governance");
      return;
    }

    if (metric === "email_failures") {
      scrollToOperationsTarget(
        "email-delivery-issues",
        "#email-delivery-issues .operations-delivery-issue-list article",
      );
      return;
    }

    // Quote metrics open the Requests queue filtered to match, with the
    // first matching active request selected in the detail pane.
    setRequestView("active");
    const activeQuotes = quotes.filter((quote) => quote.status !== "closed");
    const firstMatch =
      metric === "human_review"
        ? activeQuotes.find(
          (quote) => quote.recommendation_decision?.human_review === true,
        )
        : metric === "lab_testing"
          ? activeQuotes.find(
            (quote) =>
              quote.recommendation_decision?.requires_third_party_lab === true,
          )
          : metric === "new_quotes"
            ? activeQuotes.find((quote) => quote.status === "new")
            : activeQuotes[0];

    setRecommendationTriageView(
      metric === "human_review" || metric === "lab_testing" ? metric : "all",
    );
    setSelectedQuoteId(firstMatch?.id ?? null);
    scrollToOperationsTarget("quote-queue");
  }

  // From an Inbox conversation: show its request in the Requests workspace,
  // widening the queue filters if they would hide it.
  function openRequestFromInbox(quoteId: string) {
    const quote = quotes.find((candidate) => candidate.id === quoteId);
    if (quote === undefined) {
      setError("That request isn't in the loaded request list.");
      return;
    }
    setRequestView(quote.status === "closed" ? "all" : "active");
    setRecommendationTriageView("all");
    setSelectedQuoteId(quote.id);
    scrollToOperationsTarget("quote-queue");
  }

  function openOrderFromOverview(orderId: string) {
    // Clear the search so the order is in the list before scrolling to it.
    setOrderSearch("");
    scrollToOperationsTarget("order-history", `#operations-order-${orderId}`);
  }

  function openThreadInInbox(threadId: string) {
    setInboxThreadToOpen({ threadId });
    scrollToOperationsTarget("communications-history");
  }

  return (
    <main
      id="main-content"
      tabIndex={-1}
      className="operations-shell"
      data-appearance={appearance}
    >
      <header className="operations-brand-header">
        <a
          className="brand-logo-link"
          href="#"
          aria-label="D'Acqua Dolce operations"
        >
          <span className="brand-logo-frame">
            <BrandLogo
              variant={logoVariant}
              className="brand-logo"
            />
          </span>
        </a>

        <div className="operations-header-account">
          <div className="operations-header-identity">
            {operatorName.length > 0 ? (
              <strong>{operatorName}</strong>
            ) : null}
            <span title={currentUserEmail ?? undefined}>
              {currentUserEmail ?? "Operations user"}
            </span>
          </div>

          <button
            type="button"
            className="operations-action operations-header-button"
            onClick={() => onNavigate("/")}
          >
            Customer site
          </button>

          <button
            type="button"
            className="operations-action operations-header-button"
            onClick={() => onNavigate("/account")}
          >
            Account
          </button>
        </div>
      </header>

      <nav
        id="operations-primary-nav"
        className="operations-primary-nav"
        aria-label="Operations workspaces"
      >
        <div className="operations-nav-heading">
          <strong>Operations</strong>
          <span>{visibleWorkspaces.find(({ id }) => id === activeWorkspace)?.description}</span>
        </div>
        <div className="operations-nav-links">
          {OPERATIONS_WORKSPACE_GROUPS.map((group) => {
            const groupWorkspaces = visibleWorkspaces.filter(
              (workspace) => workspace.group === group.id,
            );
            if (groupWorkspaces.length === 0) {
              return null;
            }
            return (
              <div
                key={group.id}
                className="operations-nav-group"
                role="group"
                aria-label={group.label}
              >
                <span className="operations-nav-group-label" aria-hidden="true">
                  {group.label}
                </span>
                {groupWorkspaces.map(({ id, label }) => {
                  const waiting = workspaceWaitingCounts[id];
                  return (
                    <button
                      key={id}
                      type="button"
                      className={activeWorkspace === id ? "is-active" : ""}
                      aria-pressed={activeWorkspace === id}
                      aria-controls={`operations-panel-${id}`}
                      onClick={() => chooseWorkspace(id)}
                    >
                      {label}
                      {waiting !== undefined && waiting.count > 0 ? (
                        <span
                          className="operations-nav-count"
                          title={waiting.description}
                        >
                          {waiting.count}
                          <span className="sr-only">{` ${waiting.description}`}</span>
                        </span>
                      ) : null}
                    </button>
                  );
                })}
              </div>
            );
          })}
        </div>
      </nav>

      {error !== null ? (
        <p className="operations-alert operations-error" role="alert">
          {error}
        </p>
      ) : null}

      {message !== null ? (
        <p className="operations-alert" role="status">
          {message}
        </p>
      ) : null}

      {loading ? <p role="status">Loading operations…</p> : null}

      <section
        id="operations-panel-overview"
        className="operations-workspace-panel"
        aria-label="Overview"
        hidden={activeWorkspace !== "overview"}
      >
      <NeedsYouList
        quotes={quotes}
        orders={orders}
        awaitingReplyThreads={awaitingReplyThreads}
        failedDeliveryCount={failedDeliveries.length}
        latestFailedDeliveryAt={
          failedDeliveries.reduce<string | null>(
            (latest, delivery) =>
              latest === null || delivery.created_at > latest
                ? delivery.created_at
                : latest,
            null,
          )
        }
        onOpenRequest={openRequestFromInbox}
        onOpenThread={openThreadInInbox}
        onOpenOrder={openOrderFromOverview}
        onOpenDeliveryIssues={() => {
          scrollToOperationsTarget(
            "email-delivery-issues",
            "#email-delivery-issues .operations-delivery-issue-list article",
          );
        }}
      />

      {summary !== null ? (
        <section
          className="operations-metrics"
          aria-label="Operations summary"
        >
          {[
            ["new_quotes", summary.new_quotes, "New quotes"],
            ["open_quotes", summary.open_quotes, "Open quotes"],
            [
              "human_review",
              summary.recommendation_human_review,
              "Human review",
            ],
            [
              "lab_testing",
              summary.recommendation_lab_testing,
              "Lab testing",
            ],
            ["active_products", summary.active_products, "Active systems"],
            [
              "email_failures",
              summary.failed_email_deliveries,
              "Email failures",
            ],
          ].map(([metric, value, label]) => (
            <button
              key={metric}
              type="button"
              className="operations-metric"
              onClick={() => {
                openOperationsMetric(
                  metric as Parameters<typeof openOperationsMetric>[0],
                );
              }}
              aria-label={`${label}: ${value}. Open relevant operations area.`}
            >
              <strong>{value}</strong>
              <span>{label}</span>
              <small>Open</small>
            </button>
          ))}
        </section>
      ) : null}

      {launchReadiness !== null ? (
        <details
          id="launch-readiness"
          className="operations-section operations-disclosure"
        >
          <summary className="operations-disclosure-summary">
            <span>
              <strong>Commercial launch</strong>
              <small>Readiness snapshot</small>
            </span>
          </summary>
          <div className="operations-disclosure-content">
            <section
              className="operations-sales-insights"
              aria-labelledby="launch-readiness-title"
            >
          <div className="operations-section-heading compact">
            <p className="eyebrow">Commercial launch</p>
            <h2 id="launch-readiness-title">Readiness snapshot</h2>
            <p>
              Read-only launch audit plus an enforced commerce phase gate.
              Changing launch phase is a deployment configuration action; this
              screen never bypasses tax, payment, or other checkout guards.
            </p>
          </div>

          <div className="operations-insight-lists">
            <div>
              <strong>Commerce launch gate</strong>
              <p>
                {launchReadiness.commerce_checkout_allowed ? "Open" : "Closed"}
                {" · "}
                {launchReadiness.launch_phase_label}
              </p>
              <small>
                {launchReadiness.commerce_gate_detail}
                {launchReadiness.commerce_blockers.length > 0
                  ? ` Blockers: ${launchReadiness.commerce_blockers.join(" · ")}`
                  : ""}
              </small>
            </div>
          </div>

          <div className="operations-insight-grid">
            <div>
              <strong>{launchReadiness.ready_count}</strong>
              <span>Ready</span>
              <small>Configured launch dependencies</small>
            </div>
            <div>
              <strong>{launchReadiness.action_required_count}</strong>
              <span>Action required</span>
              <small>Configuration or business input still needed</small>
            </div>
            <div>
              <strong>{launchReadiness.deferred_count}</strong>
              <span>Deferred</span>
              <small>Intentionally not commissioned yet</small>
            </div>
          </div>

          <div className="operations-insight-lists">
            {launchReadiness.checks.map((check) => (
              <div key={check.key}>
                <strong>{check.label}</strong>
                <p>
                  {check.status === "ready"
                    ? "Ready"
                    : check.status === "action_required"
                      ? "Action required"
                      : "Deferred"}
                  {" · "}
                  {check.detail}
                </p>
                <small>
                  {check.evidence.join(" · ")}
                </small>
              </div>
            ))}
          </div>

          <LaunchDependencyEvidencePanel roles={roles} />

          <p>
            Evaluated{" "}
            {new Date(launchReadiness.evaluated_at).toLocaleString()}.
          </p>
            </section>
          </div>
        </details>
      ) : null}

      {salesInsights !== null ? (
        <details
          id="assisted-sales-insights"
          className="operations-section operations-disclosure"
        >
          <summary className="operations-disclosure-summary">
            <span>
              <strong>Assisted sales</strong>
              <small>Observed request patterns</small>
            </span>
          </summary>
          <div className="operations-disclosure-content">
            <section
              className="operations-sales-insights"
              aria-labelledby="assisted-sales-insights-title"
            >
          <div className="operations-section-heading compact">
            <p className="eyebrow">Assisted sales</p>
            <h2 id="assisted-sales-insights-title">Observed request patterns</h2>
            <p>
              Read-only aggregates from structured customer requests. These
              observations do not change recommendation policy or unlock
              self-service purchasing.
            </p>
          </div>
          <div className="operations-insight-grid">
            <div>
              <strong>{salesInsights.structured_requests}</strong>
              <span>Structured requests</span>
              <small>{salesInsights.total_requests} total requests</small>
            </div>
            <div>
              <strong>{salesInsights.lab_required_requests}</strong>
              <span>Lab review required</span>
              <small>Well-water decision snapshot</small>
            </div>
            <div>
              <strong>{salesInsights.limited_utility_requests}</strong>
              <span>Limited utilities</span>
              <small>Power or drain reported unavailable</small>
            </div>
            <div>
              <strong>{salesInsights.known_hardness_requests}</strong>
              <span>Hardness value supplied</span>
              <small>Customer-provided structured context</small>
            </div>
            <div>
              <strong>{salesInsights.research_network_yes}</strong>
              <span>Filtration network signal</span>
              <small>Research-only; excluded from technical suitability</small>
            </div>
          </div>
          <div className="operations-insight-lists">
            <div>
              <strong>Source water</strong>
              <p>{salesInsights.source_water.map((item) => `${item.value}: ${item.count}`).join(" · ") || "No structured data yet"}</p>
            </div>
            <div>
              <strong>Treatment preference</strong>
              <p>{salesInsights.treatment_preference.map((item) => `${item.value}: ${item.count}`).join(" · ") || "No structured data yet"}</p>
            </div>
            <div>
              <strong>Top service ZIPs</strong>
              <p>{salesInsights.service_postal_codes.map((item) => `${item.value}: ${item.count}`).join(" · ") || "No ZIP data yet"}</p>
            </div>
          </div>
            </section>
          </div>
        </details>
      ) : null}

      <details
        id="launch-policies"
        className="operations-section operations-disclosure"
      >
        <summary className="operations-disclosure-summary">
          <span>
            <strong>Launch policies</strong>
            <small>Approved customer terms and policy versions</small>
          </span>
        </summary>
        <div className="operations-disclosure-content">
          <PolicyManagementPanel
            roles={roles}
            onPoliciesChanged={refreshOverviewData}
          />
        </div>
      </details>

      </section>

      <section
        id="operations-panel-communications"
        className="operations-workspace-panel"
        aria-label="Communications"
        hidden={activeWorkspace !== "communications"}
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
          onActiveCountChange={setActiveInboxCount}
          onOpenRequest={openRequestFromInbox}
          onAwaitingReplyChange={setAwaitingReplyThreads}
          threadToOpen={inboxThreadToOpen}
          updatedThread={requestReplyThread}
        />
      </section>

      </section>

      <section
        id="operations-panel-requests"
        className="operations-workspace-panel"
        aria-label="Customer requests"
        hidden={activeWorkspace !== "requests"}
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
                  setRequestView(option);
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
                  recommendationTriageView === option ? "is-active" : ""
                }
                aria-pressed={recommendationTriageView === option}
                onClick={() => {
                  setRecommendationTriageView(option);
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
                        setSelectedQuoteId(quote.id);
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
              <article
                key={quote.id}
                id={`operations-request-${quote.id}`}
                hidden={quote.id !== selectedRequestId}
                className="operations-quote"
                data-quote-status={quote.status}
                data-human-review={
                  quote.recommendation_decision?.human_review === true
                    ? "true"
                    : "false"
                }
                data-lab-testing={
                  quote.recommendation_decision?.requires_third_party_lab === true
                    ? "true"
                    : "false"
                }
              >
                <div className="operations-request-workspace">
                  <header className="operations-request-header">
                    <div>
                      <p className="product-meta">
                        {quote.product_name ?? "General consultation"}
                      </p>
                      <h3>{quote.name}</h3>
                    </div>
                    <span className="operations-request-created">
                      Received {new Date(quote.created_at).toLocaleString()}
                    </span>
                  </header>

                  <RequestWorkflowProgress
                    quote={quote}
                    onSetStatus={(status) => {
                      void saveQuoteStatus(quote, status);
                    }}
                    onOpenQuote={() => {
                      document
                        .getElementById(`operations-request-${quote.id}`)
                        ?.querySelector(".operations-formal-quote")
                        ?.scrollIntoView({ behavior: "smooth", block: "start" });
                    }}
                  />

                  <section className="operations-request-region">
                    <p className="operations-request-region-label">Customer</p>
                    <div className="operations-request-contact">
                      <CopyEmailButton email={quote.email} />
                      {quote.phone !== null ? (
                        <a href={`tel:${quote.phone}`}>
                          {formatUsPhoneInput(quote.phone)}
                        </a>
                      ) : null}
                      {quote.phone !== null
                      && quote.preferred_contact_method === "text" ? (
                        <a href={`sms:${quote.phone}`}>Text</a>
                      ) : null}
                      {contactMethodLabel(quote.preferred_contact_method) !== null ? (
                        <span
                          className="operations-contact-preference"
                          data-method={quote.preferred_contact_method}
                        >
                          Prefers {contactMethodLabel(quote.preferred_contact_method)?.toLowerCase()}
                        </span>
                      ) : null}
                    </div>
                  </section>

                  {quote.recommendation_decision !== null ? (
                    <section
                      className={
                        "operations-request-region "
                        + "operations-recommendation-result"
                      }
                    >
                      <div className="operations-request-region-heading">
                        <p className="operations-request-region-label">
                          Recommendation result
                        </p>
                        <span>
                          Policy v{quote.recommendation_policy_version ?? "legacy"}
                        </span>
                      </div>

                      <div className="operations-recommendation-flags">
                        <span>Guided recommendation</span>
                        {quote.recommendation_decision.human_review ? (
                          <span>Staff review required</span>
                        ) : (
                          <span>Historical automatic starting path</span>
                        )}
                        {quote.recommendation_decision.requires_third_party_lab ? (
                          <span className="is-important">
                            Third-party lab required
                          </span>
                        ) : null}
                      </div>

                      <h4>{quote.recommendation_decision.title}</h4>
                      <p>{quote.recommendation_decision.description}</p>

                      {quote.recommendation_decision.sizing ? (
                        <div className="operations-recommendation-sizing">
                          <strong>Capacity sizing</strong>
                          <span>
                            {quote.recommendation_decision.sizing.status === "inputs_complete"
                              ? "Inputs complete; verified capacity rules are still pending."
                              : `Needs more information: ${quote.recommendation_decision.sizing.missing_inputs
                                .map((input) => recommendationContextLabel(input))
                                .join(", ")}.`}
                          </span>
                        </div>
                      ) : null}

                      {quote.recommendation_decision.components.length > 0 ? (
                        <div className="operations-recommendation-components">
                          {quote.recommendation_decision.components.map(
                            (component) => (
                              <span key={component}>
                                {RECOMMENDATION_COMPONENT_LABELS[component] ?? component}
                              </span>
                            ),
                          )}
                        </div>
                      ) : null}
                    </section>
                  ) : quote.recommendation_context !== null ? (
                    <section
                      className={
                        "operations-request-region "
                        + "operations-recommendation-legacy"
                      }
                    >
                      <p className="operations-request-region-label">
                        Guided recommendation
                      </p>
                      <p>
                        This request predates decision snapshots. Review the
                        submitted context manually.
                      </p>
                    </section>
                  ) : null}

                  {quote.recommendation_context !== null ? (
                    <section className="operations-request-region">
                      <p className="operations-request-region-label">
                        Recommendation context
                      </p>
                      <dl className="operations-recommendation-context">
                        {Object.entries(quote.recommendation_context).map(
                          ([key, value]) => (
                            <div key={key}>
                              <dt>{recommendationContextLabel(key)}</dt>
                              <dd>{recommendationContextValue(key, value)}</dd>
                            </div>
                          ),
                        )}
                      </dl>
                    </section>
                  ) : null}

                  <section className="operations-request-region">
                    <p className="operations-request-region-label">Request</p>
                    {(() => {
                      const { configuration, customerMessage } =
                        splitRequestMessage(quote.message);
                      return (
                        <>
                          {configuration !== null ? (
                            <details className="operations-request-configuration">
                              <summary>
                                Requested configuration
                                <span>
                                  {configuration.split("\n")[1]?.replace(
                                    /^Catalog reference SKU:\s*/,
                                    "",
                                  ) ?? ""}
                                </span>
                              </summary>
                              <p className="operations-customer-message">
                                {configuration}
                              </p>
                            </details>
                          ) : null}
                          {customerMessage !== null ? (
                            <p className="operations-customer-message">
                              {customerMessage}
                            </p>
                          ) : (
                            <p className="operations-request-empty">
                              No customer message was provided.
                            </p>
                          )}
                        </>
                      );
                    })()}
                  </section>

                  <RequestConversation
                    quote={quote}
                    active={
                      activeWorkspace === "requests"
                      && quote.id === selectedRequestId
                    }
                    onReplied={(reply) => {
                      setRequestReplyThread(reply.thread);
                      // Emailing a new request's customer is contacting them.
                      if (
                        quote.status === "new"
                        && reply.delivery_status !== "failed"
                      ) {
                        void saveQuoteStatus(quote, "contacted");
                      }
                    }}
                    onOpenInInbox={openThreadInInbox}
                  />

                  <FormalQuoteComposer
                    quote={quote}
                    products={products}
                    canOverrideCatalogPricing={privileged}
                    onChanged={mergeFormalQuote}
                  />

                  <section
                    className={
                      "operations-request-region "
                      + "operations-request-private"
                    }
                  >
                    <div className="operations-request-region-heading">
                      <p className="operations-request-region-label">
                        Internal follow-up
                      </p>
                      <span>Private — never shown to the customer.</span>
                    </div>

                    <label className="operations-field">
                      <span className="sr-only">Internal notes</span>
                      <textarea
                        rows={3}
                        maxLength={8000}
                        placeholder="Add private follow-up notes"
                        value={
                          quoteNoteDrafts[quote.id]
                          ?? ""
                        }
                        onChange={(event) => {
                          setQuoteNoteDrafts(
                            (current) => ({
                              ...current,
                              [quote.id]:
                                event.target.value,
                            }),
                          );
                        }}
                      />
                    </label>

                    <button
                      type="button"
                      className={
                        "operations-action secondary "
                        + (
                          (
                            quoteNoteSaveStates[quote.id]
                            ?? "idle"
                          ) === "saved"
                            ? "is-saved"
                            : ""
                        )
                      }
                      disabled={
                        (
                          quoteNoteSaveStates[quote.id]
                          ?? "idle"
                        ) === "saving"
                      }
                      onClick={() => {
                        void saveQuoteNotes(quote);
                      }}
                    >
                      {(
                        quoteNoteSaveStates[quote.id]
                        ?? "idle"
                      ) === "saving"
                        ? "Saving…"
                        : (
                            quoteNoteSaveStates[quote.id]
                            ?? "idle"
                          ) === "saved"
                          ? "Saved ✓"
                          : "Save Internal Notes"}
                    </button>
                  </section>
                </div>
              </article>
            ))}
            </div>
          </div>
        )}
      </section>

      </section>

      <OrdersWorkspace
        hidden={activeWorkspace !== "orders"}
        orders={orders}
        roles={roles}
        search={orderSearch}
        onSearchChange={setOrderSearch}
        onOrderChange={(updated) => {
          setOrders((current) =>
            current.map((candidate) =>
              candidate.id === updated.id ? updated : candidate,
            ),
          );
        }}
      />

      <CatalogWorkspace
        hidden={activeWorkspace !== "catalog"}
        products={products}
        privileged={privileged}
        onProductChange={(updated) => {
          setProducts((current) => replaceProduct(current, updated));
          refreshOverviewData();
        }}
        onMessage={setMessage}
        onError={setError}
      />

      <CustomersWorkspace
        hidden={activeWorkspace !== "customers"}
        customers={customers}
        orders={orders}
        products={products}
        privileged={privileged}
        onCustomerChange={(updated) => {
          setCustomers((current) =>
            current.map((candidate) =>
              candidate.id === updated.id ? updated : candidate,
            ),
          );
        }}
        onMessage={setMessage}
        onError={setError}
      />

      <section
        id="operations-panel-installers"
        className="operations-workspace-panel"
        aria-label="Installer research"
        hidden={activeWorkspace !== "installers"}
      >
      <InstallersWorkspace
        privileged={privileged}
        onMessage={setMessage}
        onError={setError}
      />

      </section>

      <section
        id="operations-panel-staff"
        className="operations-workspace-panel"
        aria-label="Staff access"
        hidden={activeWorkspace !== "staff"}
      >
      {administrationAllowed ? (
        <StaffWorkspace
          currentUserEmail={currentUserEmail}
          onMessage={setMessage}
          onError={setError}
        />
      ) : null}

      </section>

      <section
        id="operations-panel-audit"
        className="operations-workspace-panel"
        aria-label="Audit log"
        hidden={activeWorkspace !== "audit"}
      >
      {auditLogAllowed ? (
        <AuditWorkspace />
      ) : null}

      </section>

      <footer className="site-footer operations-footer">
        <DeveloperFooterLogo
          variant={logoVariant}
          controlsOpen={developerControlsOpen}
          onToggleControls={
            onToggleDeveloperControls
          }
        />

        <div className="operations-footer-label">
          <span>Operations Workspace</span>
          <FooterCopyright />
        </div>
      </footer>
    </main>
  );
}
