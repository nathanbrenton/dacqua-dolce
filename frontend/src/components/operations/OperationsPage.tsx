import {
  type ChangeEvent,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getProfile,
  type CustomerProfile,
} from "../../api/account";

import {
  getAdministrationAccounts,
  updateAdministrationRoles,
  type AdministrationAccount,
  type WebManagedRole,
} from "../../api/administration";

import {
  getOperationsAuditEvents,
  getOperationsCommunications,
  getOperationsCatalog,
  getOperationsCustomers,
  getOperationsOrders,
  getOperationsQuotes,
  getOperationsSummary,
  updateProductInventory,
  updateProductPricing,
  updateQuoteNotes,
  updateQuoteStatus,
  type OperationsAuditEvent,
  type OperationsCommunication,
  type OperationsCustomer,
  type OperationsOrder,
  type OperationsProduct,
  type OperationsQuote,
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
import {
  CommunicationsInbox,
} from "./CommunicationsInbox";

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

const OPERATIONS_ROLES = new Set([
  "employee",
  "manager",
  "administrator",
  "developer",
]);

const PRIVILEGED_ROLES = new Set([
  "manager",
  "administrator",
  "developer",
]);

const ADMINISTRATION_ROLES = new Set([
  "administrator",
  "developer",
]);

const WEB_MANAGED_ROLES: WebManagedRole[] = [
  "employee",
  "manager",
  "administrator",
];

const QUOTE_STATUSES = [
  "new",
  "contacted",
  "quoted",
  "closed",
] as const;

const PRICING_MODES = [
  "PUBLIC",
  "MAP_LIMITED",
  "CART_ONLY",
  "PRIVATE_QUOTE",
  "LOGIN_REQUIRED",
  "NO_ONLINE_PRICE",
  "NO_ONLINE_SALE",
] as const;

const AMOUNT_REQUIRED = new Set<string>([
  "PUBLIC",
  "MAP_LIMITED",
  "CART_ONLY",
  "LOGIN_REQUIRED",
]);

const INVENTORY_STATUSES = [
  "in_stock",
  "low_stock",
  "backordered",
  "unavailable",
  "not_tracked",
] as const;

type PricingDraft = {
  mode: string;
  amount: string;
  currency: string;
};

type InventoryDraft = {
  status: string;
  quantityOnHand: string;
};

type SaveState =
  | "idle"
  | "saving"
  | "saved";

type RequestView = "active" | "closed" | "all";

function dollarsToMinor(value: string): number | null {
  const normalized = value.trim();

  if (normalized.length === 0) {
    return null;
  }

  if (!/^\d+(\.\d{1,2})?$/.test(normalized)) {
    throw new Error(
      "Enter a dollar amount with no more than two decimals.",
    );
  }

  const amount = Number(normalized);

  if (!Number.isFinite(amount)) {
    throw new Error("Enter a valid amount.");
  }

  return Math.round(amount * 100);
}

function minorToDollars(amountMinor: number | null): string {
  if (amountMinor === null) {
    return "";
  }

  return (amountMinor / 100).toFixed(2);
}

function formatMoney(
  amountMinor: number,
  currency: string,
): string {
  return new Intl.NumberFormat(
    undefined,
    {
      style: "currency",
      currency,
    },
  ).format(amountMinor / 100);
}

function lockedSelfAdminText(
  ownAccount: boolean,
  roles: WebManagedRole[],
): string {
  if (
    ownAccount
    && roles.includes("administrator")
  ) {
    return "Your own administrator role is protected from removal.";
  }

  return (
    "Customer access is preserved automatically. "
    + "Role changes are audited."
  );
}

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
    () => roles.some((role) => PRIVILEGED_ROLES.has(role)),
    [roles],
  );

  const administrationAllowed = useMemo(
    () => roles.some((role) => ADMINISTRATION_ROLES.has(role)),
    [roles],
  );

  const [summary, setSummary] =
    useState<OperationsSummary | null>(null);
  const [quotes, setQuotes] =
    useState<OperationsQuote[]>([]);
  const [requestView, setRequestView] =
    useState<RequestView>("active");
  const [communications, setCommunications] =
    useState<OperationsCommunication[]>([]);
  const [operatorProfile, setOperatorProfile] =
    useState<CustomerProfile | null>(null);
  const [auditEvents, setAuditEvents] =
    useState<OperationsAuditEvent[]>([]);
  const [auditSearch, setAuditSearch] =
    useState("");
  const [auditLoaded, setAuditLoaded] =
    useState(false);
  const [auditLoading, setAuditLoading] =
    useState(false);
  const [auditError, setAuditError] =
    useState<string | null>(null);
  const [administrationAccounts, setAdministrationAccounts] =
    useState<AdministrationAccount[]>([]);
  const [administrationSearch, setAdministrationSearch] =
    useState("");
  const [administrationLoaded, setAdministrationLoaded] =
    useState(false);
  const [administrationLoading, setAdministrationLoading] =
    useState(false);
  const [administrationError, setAdministrationError] =
    useState<string | null>(null);
  const [administrationRoleDrafts, setAdministrationRoleDrafts] =
    useState<Record<string, WebManagedRole[]>>({});
  const [administrationSaveStates, setAdministrationSaveStates] =
    useState<Record<string, SaveState>>({});
  const [customers, setCustomers] =
    useState<OperationsCustomer[]>([]);
  const [customerSearch, setCustomerSearch] =
    useState("");
  const [orders, setOrders] =
    useState<OperationsOrder[]>([]);
  const [orderSearch, setOrderSearch] =
    useState("");
  const [products, setProducts] =
    useState<OperationsProduct[]>([]);
  const [pricingDrafts, setPricingDrafts] =
    useState<Record<string, PricingDraft>>({});
  const [inventoryDrafts, setInventoryDrafts] =
    useState<Record<string, InventoryDraft>>({});
  const [quoteNoteDrafts, setQuoteNoteDrafts] =
    useState<Record<string, string>>({});
  const [error, setError] =
    useState<string | null>(null);
  const [message, setMessage] =
    useState<string | null>(null);
  const [loading, setLoading] =
    useState(true);
  const [
    pricingSaveStates,
    setPricingSaveStates,
  ] = useState<Record<string, SaveState>>({});
  const [
    inventorySaveStates,
    setInventorySaveStates,
  ] = useState<Record<string, SaveState>>({});
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
      getOperationsQuotes(),
      getOperationsCommunications(),
      getOperationsCustomers(),
      getOperationsOrders(),
      getOperationsCatalog(),
    ])
      .then(([
        summaryResult,
        quoteResult,
        communicationResult,
        customerResult,
        orderResult,
        productResult,
      ]) => {
        setSummary(summaryResult);
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

        const nextPricing: Record<string, PricingDraft> = {};
        const nextInventory: Record<string, InventoryDraft> = {};

        for (const product of productResult) {
          nextPricing[product.id] = {
            mode: product.pricing.mode,
            amount: minorToDollars(product.pricing.amount_minor),
            currency: product.pricing.currency ?? "USD",
          };

          nextInventory[product.id] = {
            status: product.inventory.status,
            quantityOnHand: String(
              product.inventory.quantity_on_hand,
            ),
          };
        }

        setPricingDrafts(nextPricing);
        setInventoryDrafts(nextInventory);
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

  async function loadAdministrationAccounts(): Promise<void> {
    if (
      !administrationAllowed
      || administrationLoaded
      || administrationLoading
    ) {
      return;
    }

    setAdministrationLoading(true);
    setAdministrationError(null);

    try {
      const result =
        await getAdministrationAccounts();

      setAdministrationAccounts(result);
      setAdministrationRoleDrafts(
        Object.fromEntries(
          result.map((account) => [
            account.id,
            WEB_MANAGED_ROLES.filter(
              (role) => account.roles.includes(role),
            ),
          ]),
        ),
      );
      setAdministrationLoaded(true);
    } catch (caught) {
      setAdministrationError(
        caught instanceof Error
          ? caught.message
          : "Unable to load user accounts.",
      );
    } finally {
      setAdministrationLoading(false);
    }
  }

  async function loadAuditEvents(): Promise<void> {
    if (
      !privileged
      || auditLoaded
      || auditLoading
    ) {
      return;
    }

    setAuditLoading(true);
    setAuditError(null);

    try {
      const result =
        await getOperationsAuditEvents();

      setAuditEvents(result);
      setAuditLoaded(true);
    } catch {
      setAuditError(
        "Unable to load audit events.",
      );
    } finally {
      setAuditLoading(false);
    }
  }

  const filteredAdministrationAccounts = useMemo(() => {
    const query =
      administrationSearch.trim().toLowerCase();

    if (query.length === 0) {
      return administrationAccounts;
    }

    return administrationAccounts.filter((account) => {
      const searchable = [
        account.email,
        account.status,
        ...account.roles,
        account.email_verified ? "verified" : "unverified",
        account.mfa_enrolled ? "mfa enrolled" : "mfa not enrolled",
      ]
        .join(" ")
        .toLowerCase();

      return searchable.includes(query);
    });
  }, [
    administrationAccounts,
    administrationSearch,
  ]);

  const filteredCustomers = useMemo(() => {
    const query =
      customerSearch.trim().toLowerCase();

    if (query.length === 0) {
      return customers;
    }

    return customers.filter((customer) => {
      const addressText =
        customer.addresses
          .flatMap((address) => [
            address.label,
            address.line1,
            address.line2 ?? "",
            address.city,
            address.region_code,
            address.postal_code,
            address.country_code,
          ])
          .join(" ");

      const searchable = [
        customer.email,
        customer.first_name ?? "",
        customer.last_name ?? "",
        customer.phone ?? "",
        customer.status,
        addressText,
      ]
        .join(" ")
        .toLowerCase();

      return searchable.includes(query);
    });
  }, [
    customers,
    customerSearch,
  ]);

  const filteredOrders = useMemo(() => {
    const query =
      orderSearch.trim().toLowerCase();

    if (query.length === 0) {
      return orders;
    }

    return orders.filter((order) => {
      const searchable = [
        order.id,
        order.status,
        order.customer.email,
        order.customer.first_name ?? "",
        order.customer.last_name ?? "",
        order.customer.phone ?? "",
        ...order.items.flatMap((item) => [
          item.sku,
          item.name,
        ]),
      ]
        .join(" ")
        .toLowerCase();

      return searchable.includes(query);
    });
  }, [
    orders,
    orderSearch,
  ]);

  const filteredAuditEvents = useMemo(() => {
    const query =
      auditSearch.trim().toLowerCase();

    if (query.length === 0) {
      return auditEvents;
    }

    return auditEvents.filter((event) => {
      const searchable = [
        event.id,
        event.actor_user_id ?? "",
        event.action,
        event.entity_type,
        event.entity_id ?? "",
        event.environment,
      ]
        .join(" ")
        .toLowerCase();

      return searchable.includes(query);
    });
  }, [
    auditEvents,
    auditSearch,
  ]);

  if (!authorized) {
    return (
      <main className="operations-shell">
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

  function toggleAdministrationRole(
    accountId: string,
    role: WebManagedRole,
    checked: boolean,
  ): void {
    setAdministrationRoleDrafts((current) => {
      const existing = current[accountId] ?? [];
      const next = checked
        ? Array.from(new Set([...existing, role]))
        : existing.filter((value) => value !== role);

      return {
        ...current,
        [accountId]: WEB_MANAGED_ROLES.filter(
          (candidate) => next.includes(candidate),
        ),
      };
    });
  }

  async function saveAdministrationRoles(
    account: AdministrationAccount,
  ): Promise<void> {
    const desiredRoles =
      administrationRoleDrafts[account.id] ?? [];

    setAdministrationError(null);
    setMessage(null);
    setAdministrationSaveStates((current) => ({
      ...current,
      [account.id]: "saving",
    }));

    try {
      const updated = await updateAdministrationRoles(
        account.id,
        desiredRoles,
      );

      setAdministrationAccounts((current) =>
        current.map((candidate) =>
          candidate.id === updated.id
            ? updated
            : candidate,
        ),
      );

      setAdministrationRoleDrafts((current) => ({
        ...current,
        [updated.id]: WEB_MANAGED_ROLES.filter(
          (role) => updated.roles.includes(role),
        ),
      }));

      setMessage(
        `Access roles saved for ${updated.email}.`,
      );
      setAdministrationSaveStates((current) => ({
        ...current,
        [account.id]: "saved",
      }));

      window.setTimeout(() => {
        setAdministrationSaveStates((current) => ({
          ...current,
          [account.id]: "idle",
        }));
      }, 1800);
    } catch (caught) {
      setAdministrationSaveStates((current) => ({
        ...current,
        [account.id]: "idle",
      }));
      setAdministrationError(
        caught instanceof Error
          ? caught.message
          : "Account role update failed.",
      );
    }
  }

  async function savePricing(product: OperationsProduct) {
    const draft = pricingDrafts[product.id];

    if (draft === undefined) {
      return;
    }

    setError(null);
    setMessage(null);
    setPricingSaveStates((current) => ({
      ...current,
      [product.id]: "saving",
    }));

    try {
      const amountMinor = AMOUNT_REQUIRED.has(draft.mode)
        ? dollarsToMinor(draft.amount)
        : null;

      if (
        AMOUNT_REQUIRED.has(draft.mode)
        && amountMinor === null
      ) {
        throw new Error("This pricing policy requires an amount.");
      }

      const updated = await updateProductPricing(product.id, {
        mode: draft.mode,
        amount_minor: amountMinor,
        currency: draft.currency,
      });

      setProducts((current) => replaceProduct(current, updated));
      setPricingDrafts((current) => ({
        ...current,
        [updated.id]: {
          mode: updated.pricing.mode,
          amount: minorToDollars(updated.pricing.amount_minor),
          currency: updated.pricing.currency ?? "USD",
        },
      }));
      setMessage(`Pricing policy saved for ${updated.sku}.`);
      setPricingSaveStates((current) => ({
        ...current,
        [product.id]: "saved",
      }));

      window.setTimeout(() => {
        setPricingSaveStates((current) => ({
          ...current,
          [product.id]: "idle",
        }));
      }, 1800);
    } catch (caught) {
      setPricingSaveStates((current) => ({
        ...current,
        [product.id]: "idle",
      }));
      setError(
        caught instanceof Error
          ? caught.message
          : "Pricing update failed.",
      );
    }
  }

  async function saveInventory(product: OperationsProduct) {
    const draft = inventoryDrafts[product.id];

    if (draft === undefined) {
      return;
    }

    setError(null);
    setMessage(null);

    const quantityOnHand = Number.parseInt(
      draft.quantityOnHand,
      10,
    );

    if (
      !Number.isInteger(quantityOnHand)
      || quantityOnHand < 0
    ) {
      setError(
        "On-hand quantity must be a non-negative integer.",
      );
      return;
    }

    setInventorySaveStates((current) => ({
      ...current,
      [product.id]: "saving",
    }));

    try {
      const updated = await updateProductInventory(
        product.id,
        {
          status: draft.status,
          quantity_on_hand: quantityOnHand,
        },
      );

      setProducts((current) => replaceProduct(current, updated));
      setInventoryDrafts((current) => ({
        ...current,
        [updated.id]: {
          status: updated.inventory.status,
          quantityOnHand: String(
            updated.inventory.quantity_on_hand,
          ),
        },
      }));
      setMessage(`Inventory saved for ${updated.sku}.`);
      setInventorySaveStates((current) => ({
        ...current,
        [product.id]: "saved",
      }));

      window.setTimeout(() => {
        setInventorySaveStates((current) => ({
          ...current,
          [product.id]: "idle",
        }));
      }, 1800);
    } catch (caught) {
      setInventorySaveStates((current) => ({
        ...current,
        [product.id]: "idle",
      }));
      setError(
        caught instanceof Error
          ? caught.message
          : "Inventory update failed.",
      );
    }
  }

  function updatePricingDraft(
    productId: string,
    field: keyof PricingDraft,
    value: string,
  ) {
    setPricingDrafts((current) => {
      const existing = current[productId];

      if (existing === undefined) {
        return current;
      }

      return {
        ...current,
        [productId]: {
          ...existing,
          [field]: value,
        },
      };
    });
  }

  function updateInventoryDraft(
    productId: string,
    field: keyof InventoryDraft,
    value: string,
  ) {
    setInventoryDrafts((current) => {
      const existing = current[productId];

      if (existing === undefined) {
        return current;
      }

      return {
        ...current,
        [productId]: {
          ...existing,
          [field]: value,
        },
      };
    });
  }

  const visibleQuotes = useMemo(() => {
    if (requestView === "all") {
      return quotes;
    }

    return quotes.filter((quote) =>
      requestView === "closed"
        ? quote.status === "closed"
        : quote.status !== "closed",
    );
  }, [quotes, requestView]);

  const requestCounts = useMemo(() => ({
    active: quotes.filter((quote) => quote.status !== "closed").length,
    closed: quotes.filter((quote) => quote.status === "closed").length,
    all: quotes.length,
  }), [quotes]);

  const failedDeliveries = useMemo(
    () => communications.filter((item) => item.status === "failed"),
    [communications],
  );

  const operatorName = [
    operatorProfile?.first_name,
    operatorProfile?.last_name,
  ]
    .filter((value): value is string => (
      typeof value === "string" && value.trim().length > 0
    ))
    .join(" ");

  const nextAction = (
    summary === null
      ? null
      : summary.new_quotes > 0
        ? {
            title: "Review new quote requests",
            detail:
              `${summary.new_quotes} new customer `
              + (
                summary.new_quotes === 1
                  ? "request needs"
                  : "requests need"
              )
              + " attention.",
            href: "#quote-queue",
          }
        : summary.failed_email_deliveries > 0
          ? {
              title: "Investigate email delivery",
              detail:
                `${summary.failed_email_deliveries} failed email `
                + (
                  summary.failed_email_deliveries === 1
                    ? "delivery requires"
                    : "deliveries require"
                )
                + " review.",
              href: "#email-delivery-issues",
            }
          : summary.open_quotes > 0
            ? {
                title: "Continue open quotes",
                detail:
                  `${summary.open_quotes} open quote `
                  + (
                    summary.open_quotes === 1
                      ? "request remains"
                      : "requests remain"
                  )
                  + " in the queue.",
                href: "#quote-queue",
              }
            : {
                title: "No urgent actions",
                detail:
                  "The current operations queues "
                  + "do not show an urgent item.",
                href: null,
              }
  );

  return (
    <main
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

      <div className="operations-workspace-label">
        <p className="eyebrow">Operations</p>
      </div>

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

      {summary !== null ? (
        <section
          className="operations-metrics"
          aria-label="Operations summary"
        >
          <article>
            <strong>{summary.new_quotes}</strong>
            <span>New quotes</span>
          </article>
          <article>
            <strong>{summary.open_quotes}</strong>
            <span>Open quotes</span>
          </article>
          <article>
            <strong>{summary.active_products}</strong>
            <span>Active systems</span>
          </article>
          <article>
            <strong>{summary.failed_email_deliveries}</strong>
            <span>Email failures</span>
          </article>
        </section>
      ) : null}

      {nextAction !== null ? (
        <section
          className="operations-next-action"
          aria-labelledby="operations-next-action-title"
        >
          <span>Next action</span>

          <div>
            <strong id="operations-next-action-title">
              {nextAction.title}
            </strong>
            <p>{nextAction.detail}</p>
          </div>

          {nextAction.href !== null ? (
            <a href={nextAction.href}>
              Open queue
            </a>
          ) : null}
        </section>
      ) : null}

      {failedDeliveries.length > 0 ? (
        <section
          id="email-delivery-issues"
          className="operations-delivery-issues"
          aria-labelledby="email-delivery-issues-title"
        >
          <div>
            <p className="eyebrow">Delivery Issues</p>
            <h2 id="email-delivery-issues-title">Failed email deliveries</h2>
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
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <section
        id="communications-history"
        className="operations-section operations-customer-inbox-section"
      >
        <CommunicationsInbox />
      </section>

      <section
        id="quote-queue"
        className="operations-section"
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

        {quotes.length === 0 ? (
          <p className="account-muted">No quote requests.</p>
        ) : visibleQuotes.length === 0 ? (
          <p className="account-muted">
            No customer requests in this view.
          </p>
        ) : (
          <div className="operations-quote-list">
            {visibleQuotes.map((quote) => (
              <article key={quote.id} className="operations-quote">
                <div className="operations-quote-main">
                  <p className="product-meta">
                    {quote.product_name ?? "General consultation"}
                  </p>
                  <h3>{quote.name}</h3>
                  <p>
                    <a href={`mailto:${quote.email}`}>{quote.email}</a>
                    {quote.phone !== null ? (
                      <>
                        {" · "}
                        <a href={`tel:${quote.phone}`}>{quote.phone}</a>
                      </>
                    ) : null}
                  </p>
                  {quote.message !== null ? (
                    <p className="operations-customer-message">
                      {quote.message}
                    </p>
                  ) : null}

                  <label className="operations-field">
                    <span>Internal notes</span>
                    <textarea
                      rows={3}
                      maxLength={8000}
                      placeholder="Private operations notes"
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

                  <small className="operations-note">
                    Private — never shown to the customer.
                  </small>

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

                  <small>
                    {new Date(quote.created_at).toLocaleString()}
                  </small>
                </div>

                <label className="operations-field">
                  <span>Status</span>
                  <select
                    value={quote.status}
                    onChange={(event: ChangeEvent<HTMLSelectElement>) => {
                      void saveQuoteStatus(quote, event.target.value);
                    }}
                  >
                    {QUOTE_STATUSES.map((quoteStatus) => (
                      <option key={quoteStatus} value={quoteStatus}>
                        {quoteStatus}
                      </option>
                    ))}
                  </select>
                </label>
              </article>
            ))}
          </div>
        )}
      </section>

      <section
        id="order-history"
        className="operations-section"
      >
        <div className="operations-section-heading">
          <p className="eyebrow">Order History</p>
          <h2>Customer orders</h2>
          <p>
            Read-only order history tied to registered customer
            accounts. Payment-provider details are not exposed.
          </p>
        </div>

        <label
          className={
            "operations-field "
            + "operations-customer-search"
          }
        >
          <span>Search orders</span>
          <input
            type="search"
            placeholder="Customer, email, order ID, SKU, status…"
            value={orderSearch}
            onChange={(event) => {
              setOrderSearch(
                event.target.value,
              );
            }}
          />
        </label>

        {orders.length === 0 ? (
          <p className="account-muted">
            No customer orders recorded.
          </p>
        ) : filteredOrders.length === 0 ? (
          <p className="account-muted">
            No orders match this search.
          </p>
        ) : (
          <div className="operations-customer-list">
            {filteredOrders.map((order) => {
              const customerName = [
                order.customer.first_name,
                order.customer.last_name,
              ]
                .filter(
                  (value): value is string =>
                    value !== null,
                )
                .join(" ");

              return (
                <article
                  key={order.id}
                  className="operations-customer"
                >
                  <header>
                    <div>
                      <p className="product-meta">
                        Order · {order.status}
                      </p>

                      <h3>
                        {customerName || order.customer.email}
                      </h3>

                      {customerName.length > 0 ? (
                        <p>
                          <a
                            href={`mailto:${order.customer.email}`}
                          >
                            {order.customer.email}
                          </a>
                        </p>
                      ) : null}

                      {order.customer.phone !== null ? (
                        <p>
                          <a
                            href={`tel:${order.customer.phone}`}
                          >
                            {formatUsPhoneInput(
                              order.customer.phone,
                            )}
                          </a>
                        </p>
                      ) : null}

                      <small>
                        {new Date(
                          order.created_at,
                        ).toLocaleString()}
                        {" · "}
                        {order.id}
                      </small>
                    </div>
                  </header>

                  <div className="operations-address-list">
                    {order.items.map((item, index) => (
                      <div
                        key={
                          `${order.id}-${item.sku}-${index}`
                        }
                        className="operations-address"
                      >
                        <strong>
                          {item.name}
                        </strong>

                        <address>
                          {item.sku}
                          <br />
                          {item.quantity} × {formatMoney(
                            item.unit_amount_minor,
                            item.currency,
                          )}
                        </address>

                        <small>
                          Line total: {formatMoney(
                            item.line_total_minor,
                            item.currency,
                          )}
                        </small>
                      </div>
                    ))}

                    <div className="operations-address">
                      <strong>
                        Order total
                      </strong>

                      <address>
                        {formatMoney(
                          order.total_amount_minor,
                          order.currency,
                        )}
                      </address>

                      <small>
                        Read-only
                      </small>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      <details
        id="catalog-governance"
        className="operations-section operations-disclosure"
      >
        <summary className="operations-disclosure-summary">
          <span>
            <strong>Pricing & inventory</strong>
            <small>Catalog governance</small>
          </span>
        </summary>

        <div className="operations-disclosure-content">

        <div className="operations-section-heading">
          <p className="eyebrow">Catalog Governance</p>
          <h2>Pricing &amp; inventory</h2>
          <p>
            Enter only authoritative business/manufacturer data.
            Restricted products should use a non-public pricing policy
            rather than a workaround.
          </p>
        </div>

        <div className="operations-product-list">
          {products.map((product) => {
            const pricing = pricingDrafts[product.id];
            const inventory = inventoryDrafts[product.id];

            if (pricing === undefined || inventory === undefined) {
              return null;
            }

            const amountNeeded = AMOUNT_REQUIRED.has(pricing.mode);
            const pricingSaveState =
              pricingSaveStates[product.id]
              ?? "idle";
            const inventorySaveState =
              inventorySaveStates[product.id]
              ?? "idle";

            return (
              <article key={product.id} className="operations-product">
                <header>
                  <p className="product-meta">
                    {product.manufacturer}
                    {" · "}
                    {product.category}
                  </p>
                  <h3>{product.name}</h3>
                  <code>{product.sku}</code>

                  <p className="operations-note">
                    Online sale:{" "}
                    {product.online_sale_approved
                      ? "approved"
                      : (
                          "blocked pending manufacturer/"
                          + "component policy verification"
                        )}
                  </p>
                </header>

                <div className="operations-product-grid">
                  <fieldset>
                    <legend>Pricing policy</legend>

                    <label className="operations-field">
                      <span>Mode</span>
                      <select
                        value={pricing.mode}
                        disabled={!privileged}
                        onChange={(event: ChangeEvent<HTMLSelectElement>) => {
                          updatePricingDraft(
                            product.id,
                            "mode",
                            event.target.value,
                          );
                        }}
                      >
                        {PRICING_MODES.map((mode) => (
                          <option key={mode} value={mode}>
                            {mode}
                          </option>
                        ))}
                      </select>
                    </label>

                    <div className="operations-field-row">
                      <label className="operations-field">
                        <span>Amount</span>
                        <input
                          inputMode="decimal"
                          placeholder={amountNeeded ? "0.00" : "Hidden"}
                          value={amountNeeded ? pricing.amount : ""}
                          disabled={!privileged || !amountNeeded}
                          onChange={(event: ChangeEvent<HTMLInputElement>) => {
                            updatePricingDraft(
                              product.id,
                              "amount",
                              event.target.value,
                            );
                          }}
                        />
                      </label>

                      <label className="operations-field">
                        <span>Currency</span>
                        <input
                          maxLength={3}
                          value={pricing.currency}
                          disabled={!privileged}
                          onChange={(event: ChangeEvent<HTMLInputElement>) => {
                            updatePricingDraft(
                              product.id,
                              "currency",
                              event.target.value.toUpperCase(),
                            );
                          }}
                        />
                      </label>
                    </div>

                    <button
                      type="button"
                      className={
                        "operations-action "
                        + (
                          pricingSaveState === "saved"
                            ? "is-saved"
                            : ""
                        )
                      }
                      disabled={
                        !privileged
                        || pricingSaveState === "saving"
                      }
                      onClick={() => void savePricing(product)}
                    >
                      {pricingSaveState === "saving"
                        ? "Saving…"
                        : pricingSaveState === "saved"
                          ? "Saved ✓"
                          : "Save Pricing Policy"}
                    </button>

                    {!privileged ? (
                      <p className="operations-note">
                        Manager, administrator, or developer role required
                        to change pricing.
                      </p>
                    ) : null}
                  </fieldset>

                  <fieldset>
                    <legend>Inventory</legend>

                    <label className="operations-field">
                      <span>Status</span>
                      <select
                        value={inventory.status}
                        onChange={(event: ChangeEvent<HTMLSelectElement>) => {
                          updateInventoryDraft(
                            product.id,
                            "status",
                            event.target.value,
                          );
                        }}
                      >
                        {INVENTORY_STATUSES.map((inventoryStatus) => (
                          <option
                            key={inventoryStatus}
                            value={inventoryStatus}
                          >
                            {inventoryStatus}
                          </option>
                        ))}
                      </select>
                    </label>

                    <div className="operations-field-row">
                      <label className="operations-field">
                        <span>On hand</span>
                        <input
                          type="number"
                          min={0}
                          step={1}
                          value={inventory.quantityOnHand}
                          onChange={(event: ChangeEvent<HTMLInputElement>) => {
                            updateInventoryDraft(
                              product.id,
                              "quantityOnHand",
                              event.target.value,
                            );
                          }}
                        />
                      </label>

                      <label className="operations-field">
                        <span>Reserved · automatic</span>
                        <input
                          type="number"
                          min={0}
                          step={1}
                          value={
                            product.inventory.quantity_reserved
                          }
                          readOnly
                          aria-readonly="true"
                        />
                        <small>
                          Active, unexpired cart holds
                        </small>
                      </label>
                    </div>

                    <button
                      type="button"
                      className={
                        "operations-action secondary "
                        + (
                          inventorySaveState === "saved"
                            ? "is-saved"
                            : ""
                        )
                      }
                      disabled={
                        inventorySaveState === "saving"
                      }
                      onClick={() => void saveInventory(product)}
                    >
                      {inventorySaveState === "saving"
                        ? "Saving…"
                        : inventorySaveState === "saved"
                          ? "Saved ✓"
                          : "Save Inventory"}
                    </button>
                  </fieldset>
                </div>
              </article>
            );
          })}
        </div>

        </div>
      </details>

      <details
        id="customer-roster"
        className="operations-section operations-disclosure"
      >
        <summary className="operations-disclosure-summary">
          <span>
            <strong>Accounts & address book</strong>
            <small>Customer roster</small>
          </span>
        </summary>

        <div className="operations-disclosure-content">

        <div className="operations-section-heading">
          <p className="eyebrow">Customer Roster</p>
          <h2>Accounts &amp; address book</h2>
          <p>
            Registered customer accounts and saved addresses.
            This P0 view is read-only.
          </p>
        </div>

        <label
          className={
            "operations-field "
            + "operations-customer-search"
          }
        >
          <span>Search customers</span>
          <input
            type="search"
            placeholder="Name, email, phone, city, ZIP…"
            value={customerSearch}
            onChange={(event) => {
              setCustomerSearch(
                event.target.value,
              );
            }}
          />
        </label>

        {customers.length === 0 ? (
          <p className="account-muted">
            No registered customer accounts.
          </p>
        ) : filteredCustomers.length === 0 ? (
          <p className="account-muted">
            No customers match this search.
          </p>
        ) : (
          <div className="operations-customer-list">
            {filteredCustomers.map((customer) => {
              const fullName = [
                customer.first_name,
                customer.last_name,
              ]
                .filter(
                  (value): value is string =>
                    value !== null,
                )
                .join(" ");

              return (
                <article
                  key={customer.id}
                  className="operations-customer"
                >
                  <header>
                    <div>
                      <p className="product-meta">
                        Account · {customer.status}
                      </p>

                      <h3>
                        {fullName || customer.email}
                      </h3>

                      {fullName.length > 0 ? (
                        <p>
                          <a
                            href={
                              `mailto:${customer.email}`
                            }
                          >
                            {customer.email}
                          </a>
                        </p>
                      ) : null}

                      {customer.phone !== null ? (
                        <p>
                          <a
                            href={
                              `tel:${customer.phone}`
                            }
                          >
                            {formatUsPhoneInput(
                              customer.phone,
                            )}
                          </a>
                        </p>
                      ) : null}

                      <small>
                        Account created{" "}
                        {new Date(
                          customer.created_at,
                        ).toLocaleDateString()}
                      </small>
                    </div>
                  </header>

                  <div className="operations-address-list">
                    {customer.addresses.length === 0 ? (
                      <p className="account-muted">
                        No saved addresses.
                      </p>
                    ) : (
                      customer.addresses.map(
                        (address) => (
                          <div
                            key={address.id}
                            className="operations-address"
                          >
                            <strong>
                              {address.label}
                            </strong>

                            <address>
                              {address.line1}

                              {address.line2 !== null ? (
                                <>
                                  <br />
                                  {address.line2}
                                </>
                              ) : null}

                              <br />
                              {address.city},{" "}
                              {address.region_code}{" "}
                              {address.postal_code}
                              <br />
                              {address.country_code}
                            </address>

                            {(
                              address.is_default_shipping
                              || address.is_default_billing
                            ) ? (
                              <small>
                                {address.is_default_shipping
                                  ? "Default shipping"
                                  : ""}

                                {(
                                  address.is_default_shipping
                                  && address.is_default_billing
                                )
                                  ? " · "
                                  : ""}

                                {address.is_default_billing
                                  ? "Default billing"
                                  : ""}
                              </small>
                            ) : null}
                          </div>
                        )
                      )
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        )}

        </div>
      </details>

      {administrationAllowed ? (
        <details
          id="account-administration"
          className="operations-section operations-disclosure"
          onToggle={(event) => {
            if (
              event.currentTarget.open
              && !administrationLoaded
            ) {
              void loadAdministrationAccounts();
            }
          }}
        >
          <summary className="operations-disclosure-summary">
            <span>
              <strong>User access &amp; roles</strong>
              <small>Administrator account management</small>
            </span>
          </summary>

          <div className="operations-disclosure-content">
            <div className="operations-section-heading">
              <p className="eyebrow">Account Administration</p>
              <h2>User access &amp; roles</h2>
              <p>
                Customer registration remains self-service. Employee,
                manager, and administrator access is granted here.
                Developer access remains local-only.
              </p>
            </div>

            {administrationLoading ? (
              <p className="account-muted">
                Loading user accounts…
              </p>
            ) : administrationError !== null ? (
              <p
                className="operations-alert operations-error"
                role="alert"
              >
                {administrationError}
              </p>
            ) : (
              <>
                <label
                  className={
                    "operations-field "
                    + "operations-customer-search"
                  }
                >
                  <span>Search user accounts</span>
                  <input
                    type="search"
                    placeholder="Email, status, role…"
                    value={administrationSearch}
                    onChange={(event) => {
                      setAdministrationSearch(
                        event.target.value,
                      );
                    }}
                  />
                </label>

                {administrationAccounts.length === 0 ? (
                  <p className="account-muted">
                    No persisted user accounts.
                  </p>
                ) : filteredAdministrationAccounts.length === 0 ? (
                  <p className="account-muted">
                    No accounts match this search.
                  </p>
                ) : (
                  <div className="operations-customer-list">
                    {filteredAdministrationAccounts.map((account) => {
                      const roleDraft =
                        administrationRoleDrafts[account.id]
                        ?? [];
                      const developerManaged =
                        account.roles.includes("developer");
                      const ownAccount = (
                        currentUserEmail !== null
                        && account.email.toLowerCase()
                          === currentUserEmail.toLowerCase()
                      );
                      const saveState =
                        administrationSaveStates[account.id]
                        ?? "idle";

                      return (
                        <article
                          key={account.id}
                          className="operations-customer"
                        >
                          <header>
                            <div>
                              <p className="product-meta">
                                Account · {account.status}
                              </p>
                              <h3>{account.email}</h3>
                              <small>
                                Created{" "}
                                {new Date(
                                  account.created_at,
                                ).toLocaleString()}
                                {account.last_login_at !== null
                                  ? ` · Last login ${new Date(
                                      account.last_login_at,
                                    ).toLocaleString()}`
                                  : " · Never logged in"}
                              </small>
                            </div>
                          </header>

                          <div className="operations-address-list">
                            <div className="operations-address">
                              <strong>Identity</strong>
                              <address>
                                Email {account.email_verified
                                  ? "verified"
                                  : "not verified"}
                                <br />
                                MFA {account.mfa_required
                                  ? account.mfa_enrolled
                                    ? "required · enrolled"
                                    : "required · enrollment pending"
                                  : "not required"}
                              </address>
                              <small>
                                Persisted roles:{" "}
                                {account.roles.length > 0
                                  ? account.roles.join(", ")
                                  : "none"}
                              </small>
                            </div>

                            <div className="operations-address">
                              <strong>Operations roles</strong>

                              {WEB_MANAGED_ROLES.map((role) => {
                                const lockedSelfAdmin = (
                                  ownAccount
                                  && role === "administrator"
                                  && roleDraft.includes(role)
                                );

                                return (
                                  <label key={role}>
                                    <input
                                      type="checkbox"
                                      checked={roleDraft.includes(role)}
                                      disabled={
                                        developerManaged
                                        || lockedSelfAdmin
                                        || saveState === "saving"
                                      }
                                      onChange={(event) => {
                                        toggleAdministrationRole(
                                          account.id,
                                          role,
                                          event.target.checked,
                                        );
                                      }}
                                    />{" "}
                                    {role}
                                  </label>
                                );
                              })}

                              <button
                                type="button"
                                className={
                                  "operations-action secondary "
                                  + (
                                    saveState === "saved"
                                      ? "is-saved"
                                      : ""
                                  )
                                }
                                disabled={
                                  developerManaged
                                  || saveState === "saving"
                                }
                                onClick={() => {
                                  void saveAdministrationRoles(account);
                                }}
                              >
                                {saveState === "saving"
                                  ? "Saving…"
                                  : saveState === "saved"
                                    ? "Saved ✓"
                                    : "Save Roles"}
                              </button>

                              <small>
                                {developerManaged
                                  ? "Developer roles are managed locally, not from the web console."
                                  : lockedSelfAdminText(
                                      ownAccount,
                                      roleDraft,
                                    )}
                              </small>
                            </div>
                          </div>
                        </article>
                      );
                    })}
                  </div>
                )}
              </>
            )}
          </div>
        </details>
      ) : null}

      {privileged ? (
        <section
          id="audit-events"
          className="operations-section operations-audit-section"
        >
          <details
            className="operations-audit-disclosure operations-disclosure"
            onToggle={(event) => {
              if (
                event.currentTarget.open
                && !auditLoaded
              ) {
                void loadAuditEvents();
              }
            }}
          >
            <summary>
              <span>
                <strong>Audit log</strong>
                <small>
                  Privileged troubleshooting and scheduled review
                </small>
              </span>
            </summary>

            <div className="operations-audit-content">
              <div className="operations-section-heading">
                <p className="eyebrow">
                  Audit Events
                </p>
                <h2>Privileged activity history</h2>
                <p>
                  Sensitive metadata, IP addresses, and user-agent
                  details are intentionally excluded.
                </p>
              </div>

              {auditLoading ? (
                <p className="account-muted">
                  Loading audit events…
                </p>
              ) : auditError !== null ? (
                <p className="account-muted">
                  {auditError}
                </p>
              ) : (
                <>
                  <label
                    className={
                      "operations-field "
                      + "operations-customer-search"
                    }
                  >
                    <span>Search audit events</span>
                    <input
                      type="search"
                      placeholder={
                        "Action, entity, actor, environment…"
                      }
                      value={auditSearch}
                      onChange={(event) => {
                        setAuditSearch(
                          event.target.value,
                        );
                      }}
                    />
                  </label>

                  {auditEvents.length === 0 ? (
                    <p className="account-muted">
                      No audit events recorded.
                    </p>
                  ) : filteredAuditEvents.length === 0 ? (
                    <p className="account-muted">
                      No audit events match this search.
                    </p>
                  ) : (
                    <div className="operations-customer-list">
                      {filteredAuditEvents.map((event) => (
                        <article
                          key={event.id}
                          className="operations-customer"
                        >
                          <header>
                            <div>
                              <p className="product-meta">
                                {event.environment}
                                {" · "}
                                {event.entity_type}
                              </p>

                              <h3>{event.action}</h3>

                              <small>
                                {new Date(
                                  event.created_at,
                                ).toLocaleString()}
                              </small>
                            </div>
                          </header>

                          <div className="operations-address-list">
                            <div className="operations-address">
                              <strong>Entity</strong>
                              <address>
                                {event.entity_type}
                                <br />
                                {event.entity_id
                                  ?? "No entity identifier"}
                              </address>
                            </div>

                            <div className="operations-address">
                              <strong>Actor</strong>
                              <address>
                                {event.actor_user_id
                                  ?? "System / unauthenticated"}
                              </address>
                              <small>
                                Audit event {event.id}
                              </small>
                            </div>
                          </div>
                        </article>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          </details>
        </section>
      ) : null}

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
