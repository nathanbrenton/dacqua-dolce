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
};

export type CatalogProduct = {
  id: string;
  name: string;
  slug: string;
  sku: string;
  description: string;
  product_family: string | null;
  manufacturer: string;
  category: string;
  public_path: string;
  primary_image: CatalogImage | null;
  pricing: CatalogPricing;
};

export type CatalogProductDetail =
  CatalogProduct & {
    images: CatalogImage[];
    variants: CatalogVariant[];
    documents: CatalogDocument[];
    specifications: CatalogSpecification[];
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
