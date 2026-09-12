import {
  getCsrfToken,
} from "./authentication";

export type OperationsSummary = {
  new_quotes: number;
  open_quotes: number;
  active_products: number;
  failed_email_deliveries: number;
};

export type OperationsAuditEvent = {
  id: string;
  actor_user_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  environment: string;
  created_at: string;
};

export type OperationsCommunication = {
  id: string;
  category: string;
  related_entity_type: string | null;
  related_entity_id: string | null;
  sender: string;
  recipient: string;
  subject: string;
  status: string;
  created_at: string;
  sent_at: string | null;
};

export type OperationsQuote = {
  id: string;
  product_id: string | null;
  product_name: string | null;
  name: string;
  email: string;
  phone: string | null;
  message: string | null;
  internal_notes: string | null;
  status: string;
  created_at: string;
};

export type OperationsCustomerAddress = {
  id: string;
  label: string;
  line1: string;
  line2: string | null;
  city: string;
  region_code: string;
  postal_code: string;
  country_code: string;
  is_default_shipping: boolean;
  is_default_billing: boolean;
};

export type OperationsCustomer = {
  id: string;
  email: string;
  status: string;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  addresses: OperationsCustomerAddress[];
  created_at: string;
};

export type OperationsOrderCustomer = {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
};

export type OperationsOrderItem = {
  sku: string;
  name: string;
  quantity: number;
  unit_amount_minor: number;
  line_total_minor: number;
  currency: string;
};

export type OperationsOrder = {
  id: string;
  status: string;
  total_amount_minor: number;
  currency: string;
  created_at: string;
  customer: OperationsOrderCustomer;
  items: OperationsOrderItem[];
};

export type OperationsPricing = {
  mode: string;
  amount_minor: number | null;
  currency: string | null;
  effective_from: string | null;
};

export type OperationsInventory = {
  status: string;
  quantity_on_hand: number;
  quantity_reserved: number;
};

export type OperationsProduct = {
  id: string;
  sku: string;
  name: string;
  category: string;
  manufacturer: string;
  active: boolean;
  pricing: OperationsPricing;
  inventory: OperationsInventory;
};

const JSON_HEADERS = {
  "Content-Type": "application/json",
};

async function readError(
  response: Response,
): Promise<string> {
  try {
    const payload =
      (await response.json()) as {
        detail?: string;
      };

    if (
      typeof payload.detail
      === "string"
    ) {
      return payload.detail;
    }
  } catch {
    // Fall through.
  }

  return (
    `Operations request failed: `
    + `${response.status}`
  );
}

async function getJson<T>(
  path: string,
): Promise<T> {
  const response = await fetch(
    path,
    {
      credentials: "include",
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      await readError(response),
    );
  }

  return response.json() as Promise<T>;
}

async function writeJson<T>(
  path: string,
  method: "PATCH" | "PUT",
  payload: unknown,
): Promise<T> {
  const csrfToken =
    await getCsrfToken();

  const response = await fetch(
    path,
    {
      method,
      credentials: "include",
      cache: "no-store",
      headers: {
        ...JSON_HEADERS,
        "X-CSRF-Token":
          csrfToken,
      },
      body: JSON.stringify(
        payload,
      ),
    },
  );

  if (!response.ok) {
    throw new Error(
      await readError(response),
    );
  }

  return response.json() as Promise<T>;
}

export function getOperationsSummary(): Promise<OperationsSummary> {
  return getJson(
    "/api/operations/summary",
  );
}

export function getOperationsAuditEvents(): Promise<
  OperationsAuditEvent[]
> {
  return getJson(
    "/api/operations/audit-events",
  );
}

export function getOperationsCommunications(): Promise<
  OperationsCommunication[]
> {
  return getJson(
    "/api/operations/communications",
  );
}

export function getOperationsQuotes(): Promise<OperationsQuote[]> {
  return getJson(
    "/api/operations/quotes",
  );
}

export function updateQuoteStatus(
  quoteId: string,
  status: string,
): Promise<OperationsQuote> {
  return writeJson(
    `/api/operations/quotes/${encodeURIComponent(quoteId)}`,
    "PATCH",
    { status },
  );
}

export function updateQuoteNotes(
  quoteId: string,
  internalNotes: string | null,
): Promise<OperationsQuote> {
  return writeJson(
    `/api/operations/quotes/${encodeURIComponent(quoteId)}/notes`,
    "PUT",
    {
      internal_notes: internalNotes,
    },
  );
}

export function getOperationsCustomers(): Promise<OperationsCustomer[]> {
  return getJson(
    "/api/operations/customers",
  );
}

export function getOperationsOrders(): Promise<OperationsOrder[]> {
  return getJson(
    "/api/operations/orders",
  );
}

export function getOperationsCatalog(): Promise<OperationsProduct[]> {
  return getJson(
    "/api/operations/catalog",
  );
}

export function updateProductPricing(
  productId: string,
  payload: {
    mode: string;
    amount_minor: number | null;
    currency: string;
  },
): Promise<OperationsProduct> {
  return writeJson(
    `/api/operations/products/${encodeURIComponent(productId)}/pricing`,
    "PUT",
    payload,
  );
}

export function updateProductInventory(
  productId: string,
  payload: {
    status: string;
    quantity_on_hand: number;
  },
): Promise<OperationsProduct> {
  return writeJson(
    `/api/operations/products/${encodeURIComponent(productId)}/inventory`,
    "PUT",
    payload,
  );
}
