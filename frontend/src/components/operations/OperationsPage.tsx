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
  createProductRelationship,
  createCustomerEquipment,
  deleteProductRelationship,
  updateProductInventory,
  updateCustomerEquipment,
  updateProductRelationship,
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

function CopyEmailButton({ email }: { email: string }) {
  const [copied, setCopied] = useState(false);

  async function copyEmail(): Promise<void> {
    try {
      await navigator.clipboard.writeText(email);
      setCopied(true);
      window.setTimeout(() => {
        setCopied(false);
      }, 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <span className="operations-email-action">
      <span>{email}</span>
      <button
        type="button"
        className="operations-copy-email"
        onClick={() => {
          void copyEmail();
        }}
      >
        {copied ? "Copied" : "Copy email"}
      </button>
    </span>
  );
}

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

function recommendationContextValue(value: unknown): string {
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

const PRICING_MODE_LABELS: Record<string, string> = {
  PUBLIC: "Public price",
  MAP_LIMITED: "MAP-limited",
  CART_ONLY: "Cart only",
  PRIVATE_QUOTE: "Private quote",
  LOGIN_REQUIRED: "Login required",
  NO_ONLINE_PRICE: "No online price",
  NO_ONLINE_SALE: "No online sale",
};

const INVENTORY_STATUS_LABELS: Record<string, string> = {
  in_stock: "In stock",
  low_stock: "Low stock",
  backordered: "Backordered",
  unavailable: "Unavailable",
  not_tracked: "Not tracked",
};

const AUDIT_ACTION_LABELS: Record<string, string> = {
  "customer.equipment_recorded": "Installed equipment recorded",
  "customer.equipment_updated": "Installed equipment updated",
  "account.registered": "Account registered",
  "authentication.failed": "Authentication failed",
  "authentication.logout": "Signed out",
  "authentication.session_revoked": "Session revoked",
  "cart.item_added": "Cart item added",
  "cart.item_removed": "Cart item removed",
  "catalog.inventory_changed": "Inventory changed",
  "catalog.pricing_changed": "Pricing policy changed",
  "catalog.relationship_created": "Product relationship created",
  "catalog.relationship_changed": "Product relationship changed",
  "catalog.relationship_removed": "Product relationship removed",
  "communications.reply_attempted": "Customer reply attempted",
  "communications.thread_status_changed": "Inbox thread status changed",
  "customer.address_created": "Customer address created",
  "customer.address_deleted": "Customer address deleted",
  "customer.profile_updated": "Customer profile updated",
  "identity.operations_roles_changed": "Operations roles changed",
  "order.status_changed": "Order status changed",
  "quote.notes_updated": "Request notes updated",
  "quote.requested": "Customer request submitted",
  "quote.status_changed": "Request status changed",
};

const AUDIT_ENTITY_LABELS: Record<string, string> = {
  cart_item: "Cart item",
  communication_thread: "Communication thread",
  customer_address: "Customer address",
  customer_equipment: "Customer equipment",
  customer_profile: "Customer profile",
  order: "Order",
  product: "Product",
  product_relationship: "Product relationship",
  quote_request: "Customer request",
  user: "User account",
  user_session: "User session",
};

function auditActionLabel(action: string): string {
  return AUDIT_ACTION_LABELS[action] ?? action.replaceAll("_", " ");
}

function auditEntityLabel(entityType: string): string {
  return AUDIT_ENTITY_LABELS[entityType] ?? entityType.replaceAll("_", " ");
}

function roleLabel(role: string): string {
  return role.charAt(0).toUpperCase() + role.slice(1);
}

type PricingDraft = {
  mode: string;
  amount: string;
  currency: string;
};

type InventoryDraft = {
  status: string;
  quantityOnHand: string;
  estimatedLeadTime: string;
};


type EquipmentDraft = {
  productId: string;
  variantId: string;
  serialNumber: string;
  locationLabel: string;
  installedOn: string;
  lastServiceOn: string;
  nextServiceDueOn: string;
};

const EMPTY_EQUIPMENT_DRAFT: EquipmentDraft = {
  productId: "",
  variantId: "",
  serialNumber: "",
  locationLabel: "",
  installedOn: "",
  lastServiceOn: "",
  nextServiceDueOn: "",
};

type SaveState =
  | "idle"
  | "saving"
  | "saved";

type RequestView = "active" | "closed" | "all";
type RecommendationTriageView =
  | "all"
  | "guided"
  | "human_review"
  | "lab_testing";

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
  const [recommendationTriageView, setRecommendationTriageView] =
    useState<RecommendationTriageView>("all");
  const [communications, setCommunications] =
    useState<OperationsCommunication[]>([]);
  const [operatorProfile, setOperatorProfile] =
    useState<CustomerProfile | null>(null);
  const [auditEvents, setAuditEvents] =
    useState<OperationsAuditEvent[]>([]);
  const [auditSearch, setAuditSearch] =
    useState("");
  const [auditActionFilter, setAuditActionFilter] =
    useState("all");
  const [auditEntityFilter, setAuditEntityFilter] =
    useState("all");
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
  const [equipmentDraftCustomerId, setEquipmentDraftCustomerId] =
    useState<string | null>(null);
  const [equipmentDraft, setEquipmentDraft] =
    useState<EquipmentDraft>(EMPTY_EQUIPMENT_DRAFT);
  const [equipmentSaving, setEquipmentSaving] =
    useState(false);
  const [orders, setOrders] =
    useState<OperationsOrder[]>([]);
  const [orderSearch, setOrderSearch] =
    useState("");
  const [products, setProducts] =
    useState<OperationsProduct[]>([]);
  const [relationshipProductDrafts, setRelationshipProductDrafts] =
    useState<Record<string, string>>({});
  const [relationshipTypeDrafts, setRelationshipTypeDrafts] =
    useState<Record<string, "option" | "accessory">>({});
  const [relationshipSaveStates, setRelationshipSaveStates] =
    useState<Record<string, SaveState>>({});
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
            estimatedLeadTime: (
              product.inventory.estimated_lead_time ?? ""
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

  const auditActionOptions = useMemo(
    () => Array.from(new Set(auditEvents.map((event) => event.action))).sort(),
    [auditEvents],
  );

  const auditEntityOptions = useMemo(
    () => Array.from(new Set(auditEvents.map((event) => event.entity_type))).sort(),
    [auditEvents],
  );

  const filteredAuditEvents = useMemo(() => {
    const query = auditSearch.trim().toLowerCase();

    return auditEvents.filter((event) => {
      if (auditActionFilter !== "all" && event.action !== auditActionFilter) {
        return false;
      }

      if (auditEntityFilter !== "all" && event.entity_type !== auditEntityFilter) {
        return false;
      }

      if (query.length === 0) {
        return true;
      }

      const searchable = [
        event.id,
        event.actor_user_id ?? "",
        event.actor_email ?? "",
        event.action,
        auditActionLabel(event.action),
        event.entity_type,
        auditEntityLabel(event.entity_type),
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
    auditActionFilter,
    auditEntityFilter,
  ]);


  async function saveCustomerEquipment(customerId: string): Promise<void> {
    if (!equipmentDraft.productId) {
      setError("Choose a catalog product before recording equipment.");
      return;
    }
    setEquipmentSaving(true);
    setError(null);
    try {
      const updated = await createCustomerEquipment(customerId, {
        product_id: equipmentDraft.productId,
        variant_id: equipmentDraft.variantId || null,
        serial_number: equipmentDraft.serialNumber.trim() || null,
        location_label: equipmentDraft.locationLabel.trim() || null,
        installed_on: equipmentDraft.installedOn || null,
        last_service_on: equipmentDraft.lastServiceOn || null,
        next_service_due_on: equipmentDraft.nextServiceDueOn || null,
      });
      setCustomers((current) => current.map((customer) => customer.id === updated.id ? updated : customer));
      setEquipmentDraftCustomerId(null);
      setEquipmentDraft(EMPTY_EQUIPMENT_DRAFT);
      setMessage("Installed equipment recorded.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to record equipment.");
    } finally {
      setEquipmentSaving(false);
    }
  }

  async function retireCustomerEquipment(customer: OperationsCustomer, equipmentId: string): Promise<void> {
    const equipment = customer.equipment.find((item) => item.id === equipmentId);
    if (!equipment) {
      return;
    }
    setError(null);
    try {
      const updated = await updateCustomerEquipment(customer.id, equipment.id, {
        serial_number: equipment.serial_number,
        location_label: equipment.location_label,
        installed_on: equipment.installed_on,
        last_service_on: equipment.last_service_on,
        next_service_due_on: equipment.next_service_due_on,
        active: false,
      });
      setCustomers((current) => current.map((item) => item.id === updated.id ? updated : item));
      setMessage("Equipment record marked inactive.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to update equipment.");
    }
  }

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

  async function addProductRelationship(product: OperationsProduct) {
    const relatedProductId = relationshipProductDrafts[product.id] ?? "";
    const relationshipType = relationshipTypeDrafts[product.id] ?? "option";

    if (relatedProductId.length === 0) {
      setError("Choose a related catalog product first.");
      return;
    }

    setError(null);
    setMessage(null);
    setRelationshipSaveStates((current) => ({
      ...current,
      [product.id]: "saving",
    }));

    try {
      const updated = await createProductRelationship(product.id, {
        related_product_id: relatedProductId,
        relationship_type: relationshipType,
        public: false,
        active: true,
        sort_order: 0,
      });
      setProducts((current) => replaceProduct(current, updated));
      setRelationshipProductDrafts((current) => ({
        ...current,
        [product.id]: "",
      }));
      setMessage(`Internal ${relationshipType} added for ${product.sku}.`);
      setRelationshipSaveStates((current) => ({
        ...current,
        [product.id]: "saved",
      }));
    } catch (caught) {
      setRelationshipSaveStates((current) => ({
        ...current,
        [product.id]: "idle",
      }));
      setError(
        caught instanceof Error
          ? caught.message
          : "Product relationship update failed.",
      );
    }
  }

  async function changeProductRelationship(
    product: OperationsProduct,
    relationship: OperationsProduct["relationships"][number],
    changes: Partial<{ public: boolean; active: boolean }>,
  ) {
    setError(null);
    setMessage(null);

    try {
      const updated = await updateProductRelationship(
        product.id,
        relationship.id,
        {
          relationship_type: relationship.relationship_type,
          public: changes.public ?? relationship.public,
          active: changes.active ?? relationship.active,
          sort_order: relationship.sort_order,
        },
      );
      setProducts((current) => replaceProduct(current, updated));
      setMessage(`Product relationship saved for ${product.sku}.`);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Product relationship update failed.",
      );
    }
  }

  async function removeProductRelationship(
    product: OperationsProduct,
    relationshipId: string,
  ) {
    setError(null);
    setMessage(null);

    try {
      const updated = await deleteProductRelationship(
        product.id,
        relationshipId,
      );
      setProducts((current) => replaceProduct(current, updated));
      setMessage(`Product relationship removed from ${product.sku}.`);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Product relationship removal failed.",
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
          estimated_lead_time: (
            draft.estimatedLeadTime.trim() || null
          ),
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
          estimatedLeadTime: (
            updated.inventory.estimated_lead_time ?? ""
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
      : summary.recommendation_lab_testing > 0
        ? {
            title: "Review required lab testing",
            detail:
              `${summary.recommendation_lab_testing} open guided `
              + (
                summary.recommendation_lab_testing === 1
                  ? "request requires"
                  : "requests require"
              )
              + " third-party laboratory testing.",
            href: "#quote-queue",
          }
        : summary.recommendation_human_review > 0
          ? {
              title: "Review guided recommendations",
              detail:
                `${summary.recommendation_human_review} open guided `
                + (
                  summary.recommendation_human_review === 1
                    ? "request needs"
                    : "requests need"
                )
                + " human review.",
              href: "#quote-queue",
            }
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
            <strong>{summary.recommendation_human_review}</strong>
            <span>Human review</span>
          </article>
          <article>
            <strong>{summary.recommendation_lab_testing}</strong>
            <span>Lab testing</span>
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
          <div className="operations-quote-list">
            {visibleQuotes.map((quote) => (
              <article key={quote.id} className="operations-quote">
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

                  <section className="operations-request-region">
                    <p className="operations-request-region-label">Customer</p>
                    <div className="operations-request-contact">
                      <CopyEmailButton email={quote.email} />
                      {quote.phone !== null ? (
                        <a href={`tel:${quote.phone}`}>{quote.phone}</a>
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
                          <span>Human review</span>
                        ) : (
                          <span>Automatic starting path</span>
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
                              <dd>{recommendationContextValue(value)}</dd>
                            </div>
                          ),
                        )}
                      </dl>
                    </section>
                  ) : null}

                  <section className="operations-request-region">
                    <p className="operations-request-region-label">Request</p>
                    {quote.message !== null ? (
                      <p className="operations-customer-message">
                        {quote.message}
                      </p>
                    ) : (
                      <p className="operations-request-empty">
                        No customer message was provided.
                      </p>
                    )}
                  </section>

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

                <aside className="operations-request-status">
                  <div>
                    <p className="operations-request-region-label">Status</p>
                    <strong>
                      {QUOTE_STATUS_LABELS[quote.status as keyof typeof QUOTE_STATUS_LABELS] ?? quote.status}
                    </strong>
                  </div>

                  <label className="operations-field">
                    <span>Update status</span>
                    <select
                      value={quote.status}
                      onChange={(event: ChangeEvent<HTMLSelectElement>) => {
                        void saveQuoteStatus(quote, event.target.value);
                      }}
                    >
                      {QUOTE_STATUSES.map((quoteStatus) => (
                        <option key={quoteStatus} value={quoteStatus}>
                          {QUOTE_STATUS_LABELS[quoteStatus]}
                        </option>
                      ))}
                    </select>
                  </label>
                </aside>
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
                          <CopyEmailButton email={order.customer.email} />
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

                  <div className="operations-catalog-architecture">
                    <span>
                      <strong>Family</strong>
                      {product.product_family ?? "Not assigned"}
                    </span>
                    <span>
                      <strong>System</strong>
                      {product.system_type ?? "Not assigned"}
                    </span>
                    <span>
                      <strong>Active configurations</strong>
                      {product.active_variant_count}
                    </span>
                    <span>
                      <strong>Public options</strong>
                      {product.public_option_count}
                    </span>
                  </div>

                  <div className="operations-governance-badges">
                    <span>
                      Pricing: {PRICING_MODE_LABELS[product.pricing.mode] ?? product.pricing.mode}
                    </span>
                    <span>
                      Inventory: {INVENTORY_STATUS_LABELS[product.inventory.status] ?? product.inventory.status}
                    </span>
                    <span>Reserved: {product.inventory.quantity_reserved}</span>
                    <span>
                      Online sale: {product.online_sale_approved ? "approved" : "blocked"}
                    </span>
                  </div>

                  {!product.online_sale_approved ? (
                    <p className="operations-note">
                      Online sale remains blocked pending applicable manufacturer/component policy verification.
                    </p>
                  ) : null}
                </header>

                <details className="operations-product-relationships">
                  <summary>Options &amp; accessories</summary>

                  <div className="operations-product-relationship-list">
                    {product.relationships.length === 0 ? (
                      <p className="operations-note">
                        No product relationships are recorded. Add only options or accessories whose compatibility has been verified.
                      </p>
                    ) : (
                      product.relationships.map((relationship) => (
                        <div
                          key={relationship.id}
                          className="operations-product-relationship"
                        >
                          <div>
                            <strong>{relationship.related_name}</strong>
                            <code>{relationship.related_sku}</code>
                            <small>
                              {relationship.relationship_type === "option"
                                ? "Option"
                                : "Accessory"}
                              {relationship.active ? " · active" : " · inactive"}
                              {relationship.public ? " · public" : " · internal"}
                            </small>
                          </div>

                          {privileged ? (
                            <div className="operations-product-relationship-actions">
                              <button
                                type="button"
                                className="operations-action secondary"
                                onClick={() => {
                                  void changeProductRelationship(
                                    product,
                                    relationship,
                                    { public: !relationship.public },
                                  );
                                }}
                              >
                                {relationship.public ? "Make internal" : "Make public"}
                              </button>
                              <button
                                type="button"
                                className="operations-action secondary"
                                onClick={() => {
                                  void changeProductRelationship(
                                    product,
                                    relationship,
                                    { active: !relationship.active },
                                  );
                                }}
                              >
                                {relationship.active ? "Deactivate" : "Activate"}
                              </button>
                              <button
                                type="button"
                                className="operations-action secondary"
                                onClick={() => {
                                  void removeProductRelationship(
                                    product,
                                    relationship.id,
                                  );
                                }}
                              >
                                Remove
                              </button>
                            </div>
                          ) : null}
                        </div>
                      ))
                    )}
                  </div>

                  {privileged ? (
                    <div className="operations-product-relationship-create">
                      <label className="operations-field">
                        <span>Related catalog product</span>
                        <select
                          value={relationshipProductDrafts[product.id] ?? ""}
                          onChange={(event: ChangeEvent<HTMLSelectElement>) => {
                            setRelationshipProductDrafts((current) => ({
                              ...current,
                              [product.id]: event.target.value,
                            }));
                          }}
                        >
                          <option value="">Choose a product</option>
                          {products
                            .filter((candidate) => candidate.id !== product.id)
                            .map((candidate) => (
                              <option key={candidate.id} value={candidate.id}>
                                {candidate.name} · {candidate.sku}
                              </option>
                            ))}
                        </select>
                      </label>

                      <label className="operations-field">
                        <span>Relationship</span>
                        <select
                          value={relationshipTypeDrafts[product.id] ?? "option"}
                          onChange={(event: ChangeEvent<HTMLSelectElement>) => {
                            setRelationshipTypeDrafts((current) => ({
                              ...current,
                              [product.id]: event.target.value as "option" | "accessory",
                            }));
                          }}
                        >
                          <option value="option">Option</option>
                          <option value="accessory">Accessory</option>
                        </select>
                      </label>

                      <button
                        type="button"
                        className="operations-action"
                        disabled={relationshipSaveStates[product.id] === "saving"}
                        onClick={() => {
                          void addProductRelationship(product);
                        }}
                      >
                        {relationshipSaveStates[product.id] === "saving"
                          ? "Adding…"
                          : "Add as internal"}
                      </button>
                      <p className="operations-note">
                        New relationships start internal. Make them public only after compatibility and public presentation are confirmed.
                      </p>
                    </div>
                  ) : null}
                </details>

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
                            {PRICING_MODE_LABELS[mode] ?? mode}
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

                    <p className="operations-governance-context">
                      Current authoritative policy: {PRICING_MODE_LABELS[product.pricing.mode] ?? product.pricing.mode}
                      {product.pricing.amount_minor !== null
                        ? ` · ${formatMoney(product.pricing.amount_minor, product.pricing.currency ?? "USD")}`
                        : " · amount withheld"}
                    </p>

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
                            {INVENTORY_STATUS_LABELS[inventoryStatus] ?? inventoryStatus}
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

                    <label className="operations-field">
                      <span>Estimated lead time · customer-facing when out of stock</span>
                      <input
                        type="text"
                        maxLength={120}
                        placeholder="Example: 2–3 weeks"
                        value={inventory.estimatedLeadTime}
                        onChange={(event: ChangeEvent<HTMLInputElement>) => {
                          updateInventoryDraft(
                            product.id,
                            "estimatedLeadTime",
                            event.target.value,
                          );
                        }}
                      />
                      <small>
                        Leave blank until fulfillment timing is reliable.
                      </small>
                    </label>

                    <p className="operations-governance-context">
                      Authoritative stock: {product.inventory.quantity_on_hand}
                      {product.inventory.status !== "not_tracked"
                        ? ` · reserved ${product.inventory.quantity_reserved} · available ${Math.max(0, product.inventory.quantity_on_hand - product.inventory.quantity_reserved)}`
                        : " · quantity is informational while inventory is not tracked"}
                    </p>

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
            Registered customer accounts, saved addresses, and installed equipment.
            Profile and address information remains read-only here.
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

              const customerOrders = orders.filter(
                (order) => order.customer.id === customer.id,
              );
              const addressCount = customer.addresses.length;
              const orderCount = customerOrders.length;

              return (
                <article
                  key={customer.id}
                  className="operations-customer operations-account-workspace"
                >
                  <section className="operations-account-identity">
                    <div className="operations-account-heading">
                      <div>
                        <p className="product-meta">
                          Customer account
                        </p>

                        <h3>
                          {fullName || customer.email}
                        </h3>
                      </div>

                      <span className="operations-account-status">
                        {customer.status}
                      </span>
                    </div>

                    <div className="operations-account-contact">
                      <div>
                        <span>Email</span>
                        <CopyEmailButton email={customer.email} />
                      </div>

                      <div>
                        <span>Phone</span>
                        {customer.phone !== null ? (
                          <a href={`tel:${customer.phone}`}>
                            {formatUsPhoneInput(
                              customer.phone,
                            )}
                          </a>
                        ) : (
                          <strong>Not provided</strong>
                        )}
                      </div>
                    </div>

                    <div className="operations-account-facts">
                      <div>
                        <span>Saved addresses</span>
                        <strong>{addressCount}</strong>
                      </div>
                      <div>
                        <span>Recorded orders</span>
                        <strong>{orderCount}</strong>
                      </div>
                      <div>
                        <span>Installed equipment</span>
                        <strong>{customer.equipment.filter((item) => item.active).length}</strong>
                      </div>
                      <div>
                        <span>Customer since</span>
                        <strong>
                          {new Date(
                            customer.created_at,
                          ).toLocaleDateString()}
                        </strong>
                      </div>
                    </div>

                    <p className="operations-account-boundary">
                      Orders are linked by the registered customer
                      account. Customer Requests are kept separate
                      unless a durable account relationship is stored.
                    </p>
                  </section>

                  <section className="operations-account-addresses">
                    <div className="operations-account-section-heading">
                      <div>
                        <p className="product-meta">Address book</p>
                        <h4>Saved customer addresses</h4>
                      </div>
                      <small>Read-only</small>
                    </div>

                    <div className="operations-address-list">
                      {customer.addresses.length === 0 ? (
                        <div className="operations-address operations-address-empty">
                          <strong>No saved addresses</strong>
                          <p className="account-muted">
                            This customer has not saved a shipping or
                            billing address yet.
                          </p>
                        </div>
                      ) : (
                        customer.addresses.map(
                          (address) => (
                            <div
                              key={address.id}
                              className="operations-address"
                            >
                              <div className="operations-address-heading">
                                <strong>{address.label}</strong>
                                {(
                                  address.is_default_shipping
                                  || address.is_default_billing
                                ) ? (
                                  <div className="operations-address-badges">
                                    {address.is_default_shipping ? (
                                      <span>Default shipping</span>
                                    ) : null}
                                    {address.is_default_billing ? (
                                      <span>Default billing</span>
                                    ) : null}
                                  </div>
                                ) : null}
                              </div>

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
                            </div>
                          )
                        )
                      )}
                    </div>
                  </section>

                  <section className="operations-account-equipment">
                    <div className="operations-account-section-heading">
                      <div>
                        <p className="product-meta">Installed equipment</p>
                        <h4>Ownership &amp; service record</h4>
                      </div>
                      <small>{privileged ? "Managed" : "Read-only"}</small>
                    </div>

                    <div className="operations-equipment-list">
                      {customer.equipment.filter((item) => item.active).length === 0 ? (
                        <p className="account-muted">No active installed equipment is recorded.</p>
                      ) : customer.equipment.filter((item) => item.active).map((equipment) => (
                        <article key={equipment.id} className="operations-equipment-row">
                          <div>
                            <strong>{equipment.product_name}</strong>
                            <p>{equipment.variant_name ?? equipment.sku}{equipment.location_label ? ` · ${equipment.location_label}` : ""}</p>
                          </div>
                          <div className="operations-equipment-dates">
                            <span>Installed: {equipment.installed_on ?? "Not recorded"}</span>
                            <span>Last service: {equipment.last_service_on ?? "Not recorded"}</span>
                            <span>Next service: {equipment.next_service_due_on ?? "Not scheduled"}</span>
                          </div>
                          {privileged ? (
                            <button type="button" className="text-button compact" onClick={() => void retireCustomerEquipment(customer, equipment.id)}>Mark inactive</button>
                          ) : null}
                        </article>
                      ))}
                    </div>

                    {privileged ? (
                      equipmentDraftCustomerId === customer.id ? (
                        <div className="operations-equipment-form">
                          <label className="operations-field">
                            <span>Catalog product</span>
                            <select value={equipmentDraft.productId} onChange={(event) => setEquipmentDraft({ ...equipmentDraft, productId: event.target.value, variantId: "" })}>
                              <option value="">Choose product…</option>
                              {products.filter((product) => product.active).map((product) => (
                                <option key={product.id} value={product.id}>{product.product_family ? `${product.product_family} — ` : ""}{product.name}</option>
                              ))}
                            </select>
                          </label>
                          {(() => {
                            const selectedProduct = products.find((product) => product.id === equipmentDraft.productId);
                            if (!selectedProduct || selectedProduct.variants.length === 0) {
                              return null;
                            }
                            return (
                              <label className="operations-field">
                                <span>Size / configuration</span>
                                <select value={equipmentDraft.variantId} onChange={(event) => setEquipmentDraft({ ...equipmentDraft, variantId: event.target.value })}>
                                  <option value="">Not specified</option>
                                  {selectedProduct.variants.map((variant) => (
                                    <option key={variant.id} value={variant.id}>{variant.display_name} · {variant.sku}</option>
                                  ))}
                                </select>
                              </label>
                            );
                          })()}
                          <label className="operations-field"><span>Location</span><input value={equipmentDraft.locationLabel} onChange={(event) => setEquipmentDraft({ ...equipmentDraft, locationLabel: event.target.value })} placeholder="Kitchen, garage, utility room…" /></label>
                          <label className="operations-field"><span>Serial number</span><input value={equipmentDraft.serialNumber} onChange={(event) => setEquipmentDraft({ ...equipmentDraft, serialNumber: event.target.value })} /></label>
                          <div className="operations-equipment-date-grid">
                            <label className="operations-field"><span>Installed</span><input type="date" value={equipmentDraft.installedOn} onChange={(event) => setEquipmentDraft({ ...equipmentDraft, installedOn: event.target.value })} /></label>
                            <label className="operations-field"><span>Last service</span><input type="date" value={equipmentDraft.lastServiceOn} onChange={(event) => setEquipmentDraft({ ...equipmentDraft, lastServiceOn: event.target.value })} /></label>
                            <label className="operations-field"><span>Next service</span><input type="date" value={equipmentDraft.nextServiceDueOn} onChange={(event) => setEquipmentDraft({ ...equipmentDraft, nextServiceDueOn: event.target.value })} /></label>
                          </div>
                          <div className="operations-inline-actions">
                            <button type="button" className="operations-action" disabled={equipmentSaving} onClick={() => void saveCustomerEquipment(customer.id)}>{equipmentSaving ? "Saving…" : "Record equipment"}</button>
                            <button type="button" className="text-button compact" disabled={equipmentSaving} onClick={() => { setEquipmentDraftCustomerId(null); setEquipmentDraft(EMPTY_EQUIPMENT_DRAFT); }}>Cancel</button>
                          </div>
                        </div>
                      ) : (
                        <button type="button" className="operations-action secondary" onClick={() => { setEquipmentDraftCustomerId(customer.id); setEquipmentDraft(EMPTY_EQUIPMENT_DRAFT); }}>Record installed equipment</button>
                      )
                    ) : null}
                  </section>
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

                          <div className="operations-governance-badges">
                            <span>Status: {roleLabel(account.status)}</span>
                            <span>Email: {account.email_verified ? "verified" : "unverified"}</span>
                            <span>
                              MFA: {account.mfa_required
                                ? account.mfa_enrolled
                                  ? "required · enrolled"
                                  : "required · pending"
                                : "not required"}
                            </span>
                            <span>
                              Access: {account.roles.length > 0
                                ? account.roles.map(roleLabel).join(", ")
                                : "none"}
                            </span>
                          </div>

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
                                    {roleLabel(role)}
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
                  <div className="operations-audit-controls">
                    <label className="operations-field operations-customer-search">
                      <span>Search audit events</span>
                      <input
                        type="search"
                        placeholder="Action, entity, actor, environment…"
                        value={auditSearch}
                        onChange={(event) => setAuditSearch(event.target.value)}
                      />
                    </label>

                    <label className="operations-field">
                      <span>Action</span>
                      <select
                        value={auditActionFilter}
                        onChange={(event) => setAuditActionFilter(event.target.value)}
                      >
                        <option value="all">All actions</option>
                        {auditActionOptions.map((action) => (
                          <option key={action} value={action}>
                            {auditActionLabel(action)}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label className="operations-field">
                      <span>Entity</span>
                      <select
                        value={auditEntityFilter}
                        onChange={(event) => setAuditEntityFilter(event.target.value)}
                      >
                        <option value="all">All entities</option>
                        {auditEntityOptions.map((entityType) => (
                          <option key={entityType} value={entityType}>
                            {auditEntityLabel(entityType)}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>

                  <p className="operations-governance-context">
                    Showing {filteredAuditEvents.length} of {auditEvents.length} retained recent events.
                  </p>

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
                                {auditEntityLabel(event.entity_type)}
                              </p>

                              <h3>{auditActionLabel(event.action)}</h3>

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
                                {auditEntityLabel(event.entity_type)}
                                <br />
                                {event.entity_id
                                  ?? "No entity identifier"}
                              </address>
                            </div>

                            <div className="operations-address">
                              <strong>Actor</strong>
                              <address>
                                {event.actor_email
                                  ?? (event.actor_user_id
                                    ? "Employee account"
                                    : "System / unauthenticated")}
                              </address>
                              <small>
                                {event.actor_user_id
                                  ? `User ${event.actor_user_id} · `
                                  : ""}
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
