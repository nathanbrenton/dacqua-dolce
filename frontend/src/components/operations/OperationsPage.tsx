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

import {
  getOperationsCommunications,
  getOperationsCatalog,
  getOperationsCustomers,
  getOperationsLaunchReadiness,
  getOperationsOrders,
  getOperationsQuotes,
  getOperationsSalesInsights,
  getOperationsSummary,
  type OperationsCommunication,
  type OperationsCommunicationThread,
  type OperationsCommunicationThreadDetail,
  type OperationsCustomer,
  type OperationsOrder,
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
import {
  FooterCopyright,
} from "../brand/FooterCopyright";
import { AuditWorkspace } from "./workspaces/AuditWorkspace";
import { CatalogWorkspace } from "./workspaces/CatalogWorkspace";
import { CustomersWorkspace } from "./workspaces/CustomersWorkspace";
import { InboxWorkspace } from "./workspaces/InboxWorkspace";
import { InstallersWorkspace } from "./workspaces/InstallersWorkspace";
import { OrdersWorkspace } from "./workspaces/OrdersWorkspace";
import { OverviewWorkspace, type OperationsMetric } from "./workspaces/OverviewWorkspace";
import { RequestsWorkspace } from "./workspaces/RequestsWorkspace";
import { StaffWorkspace } from "./workspaces/StaffWorkspace";
import {
  type RecommendationTriageView,
  type RequestView,
} from "./requests/requestLabels";

import {
  type AppearanceMode,
} from "../../theme/appearance";
import {
  type LogoVariantId,
} from "../../theme/branding";

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
  const [error, setError] =
    useState<string | null>(null);
  const [message, setMessage] =
    useState<string | null>(null);
  const [loading, setLoading] =
    useState(true);

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

  const failedDeliveries = useMemo(
    () => communications.filter(
      (item) => item.status === "failed" && item.requires_review,
    ),
    [communications],
  );

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

  function openOperationsMetric(metric: OperationsMetric) {
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

      <OverviewWorkspace
        hidden={activeWorkspace !== "overview"}
        roles={roles}
        summary={summary}
        launchReadiness={launchReadiness}
        salesInsights={salesInsights}
        quotes={quotes}
        orders={orders}
        awaitingReplyThreads={awaitingReplyThreads}
        failedDeliveries={failedDeliveries}
        onOpenMetric={openOperationsMetric}
        onOpenRequest={openRequestFromInbox}
        onOpenThread={openThreadInInbox}
        onOpenOrder={openOrderFromOverview}
        onOpenDeliveryIssues={() => {
          scrollToOperationsTarget(
            "email-delivery-issues",
            "#email-delivery-issues .operations-delivery-issue-list article",
          );
        }}
        onPoliciesChanged={refreshOverviewData}
      />

      <InboxWorkspace
        hidden={activeWorkspace !== "communications"}
        failedDeliveries={failedDeliveries}
        onDeliveriesReviewed={(reviewed) => {
          const reviewedById = new Map(reviewed.map((item) => [item.id, item]));
          setCommunications((current) => current.map(
            (item) => reviewedById.get(item.id) ?? item,
          ));
          refreshOverviewData();
        }}
        onActiveCountChange={setActiveInboxCount}
        onAwaitingReplyChange={setAwaitingReplyThreads}
        onOpenRequest={openRequestFromInbox}
        threadToOpen={inboxThreadToOpen}
        updatedThread={requestReplyThread}
        onMessage={setMessage}
        onError={setError}
      />

      <RequestsWorkspace
        hidden={activeWorkspace !== "requests"}
        quotes={quotes}
        onQuotesChange={setQuotes}
        products={products}
        privileged={privileged}
        requestView={requestView}
        onRequestViewChange={setRequestView}
        triageView={recommendationTriageView}
        onTriageViewChange={setRecommendationTriageView}
        selectedQuoteId={selectedQuoteId}
        onSelectQuote={setSelectedQuoteId}
        onStatusSaved={refreshOverviewData}
        onReplied={setRequestReplyThread}
        onOpenThreadInInbox={openThreadInInbox}
        onMessage={setMessage}
        onError={setError}
      />

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
