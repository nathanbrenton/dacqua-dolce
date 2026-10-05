import { getCsrfToken } from "./authentication";

export type CatalogPricing = {
  mode: string;
  amount_minor: number | null;
  currency: string | null;
  display_price: boolean;
  can_add_to_cart: boolean;
  can_checkout_online: boolean;
  action: string;
  action_label: string;
};


export type CatalogAvailability = {
  status: string;
  available: boolean | null;
  action: string;
  action_label: string;
  lifecycle_status: "active" | "soon_discontinued" | "discontinued" | string;
  expected_available_on: string | null;
  estimated_lead_time: string | null;
  can_notify_when_in_stock: boolean;
  can_inquire: boolean;
};

export type CatalogImage = {
  path: string;
  alt_text: string;
};

export type CatalogSpecification = {
  spec_key: string;
  label: string;
  value_text: string;
  unit: string | null;
};

export type CatalogManufacturerClaim = {
  claim_text: string;
  source_reference: string;
  provenance_label: string;
};

export type CatalogOption = {
  id: string;
  relationship_type: "option" | "accessory" | string;
  name: string;
  slug: string;
  product_family: string | null;
  system_type: string | null;
  public_path: string;
};

export type CatalogVariant = {
  id: string;
  display_name: string;
  sku: string;
  option_values: Record<string, string>;
};

export type CatalogDocument = {
  title: string;
  document_type: string;
  path: string;
  content_type: string;
  version: string;
  verified_at: string | null;
};

export type CatalogProduct = {
  id: string;
  name: string;
  slug: string;
  sku: string;
  description: string;
  product_family: string | null;
  system_type: string | null;
  category: string;
  public_path: string;
  primary_image: CatalogImage | null;
  pricing: CatalogPricing;
  availability: CatalogAvailability;
};

export type CatalogProductDetail =
  CatalogProduct & {
    images: CatalogImage[];
    variants: CatalogVariant[];
    options_accessories: CatalogOption[];
    documents: CatalogDocument[];
    specifications: CatalogSpecification[];
    manufacturer_claims: CatalogManufacturerClaim[];
  };

type ProductListPayload = {
  products: CatalogProduct[];
};

async function readError(
  response: Response,
): Promise<string> {
  try {
    const payload = (await response.json()) as {
      detail?: string;
    };

    if (
      typeof payload.detail === "string"
    ) {
      return payload.detail;
    }
  } catch {
    // Fall through.
  }

  return (
    `Catalog request failed: ${response.status}`
  );
}

export async function getCatalogProducts(): Promise<
  CatalogProduct[]
> {
  const response = await fetch(
    "/api/catalog/products",
    {
      cache: "no-store",
      credentials: "include",
    },
  );

  if (!response.ok) {
    throw new Error(
      await readError(response),
    );
  }

  const payload =
    (await response.json()) as ProductListPayload;

  return payload.products;
}

export async function getCatalogProduct(
  slug: string,
): Promise<CatalogProductDetail> {
  const response = await fetch(
    `/api/catalog/products/${encodeURIComponent(slug)}`,
    {
      cache: "no-store",
      credentials: "include",
    },
  );

  if (!response.ok) {
    throw new Error(
      await readError(response),
    );
  }

  return response.json() as Promise<
    CatalogProductDetail
  >;
}

export async function getCatalogProductAvailability(
  slug: string,
): Promise<CatalogAvailability> {
  const response = await fetch(
    `/api/catalog/products/${encodeURIComponent(slug)}/availability`,
    {
      cache: "no-store",
      credentials: "include",
    },
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<CatalogAvailability>;
}

export async function subscribeStockNotification(
  slug: string,
  email: string,
): Promise<{ status: string; message: string }> {
  const csrfToken = await getCsrfToken();
  const response = await fetch(
    `/api/catalog/products/${encodeURIComponent(slug)}/stock-notifications`,
    {
      method: "POST",
      credentials: "include",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({ email }),
    },
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<{ status: string; message: string }>;
}

export async function cancelStockNotification(
  slug: string,
  email: string,
): Promise<{ status: string; message: string }> {
  const csrfToken = await getCsrfToken();
  const response = await fetch(
    `/api/catalog/products/${encodeURIComponent(slug)}/stock-notifications/cancel`,
    {
      method: "POST",
      credentials: "include",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({ email }),
    },
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<{ status: string; message: string }>;
}
