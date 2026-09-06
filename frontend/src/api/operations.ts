import {
  getCsrfToken,
} from "./authentication";

export type OperationsSummary = {
  new_quotes: number;
  open_quotes: number;
  active_products: number;
  failed_email_deliveries: number;
};

export type OperationsQuote = {
  id: string;
  product_id: string | null;
  product_name: string | null;
  name: string;
  email: string;
  phone: string | null;
  message: string | null;
  status: string;
  created_at: string;
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
    quantity_reserved: number;
  },
): Promise<OperationsProduct> {
  return writeJson(
    `/api/operations/products/${encodeURIComponent(productId)}/inventory`,
    "PUT",
    payload,
  );
}
