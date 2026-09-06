import { getCsrfToken } from "./authentication";

export type CartItem = {
  id: string;
  product_id: string;
  variant_id: string | null;
  sku: string;
  name: string;
  quantity: number;
  unit_amount_minor: number;
  line_total_minor: number;
  currency: string;
};

export type Cart = {
  id: string;
  status: string;
  items: CartItem[];
  total_amount_minor: number;
  currency: string | null;
};

export async function getCart(): Promise<Cart> {
  const response = await fetch(
    "/api/cart",
    {
      credentials: "include",
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Cart request failed: ${response.status}`,
    );
  }

  return response.json() as Promise<Cart>;
}

export async function addCartItem(
  productId: string,
  variantId: string | null = null,
  quantity = 1,
): Promise<Cart> {
  const csrfToken = await getCsrfToken();

  const response = await fetch(
    "/api/cart/items",
    {
      method: "POST",
      credentials: "include",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({
        product_id: productId,
        variant_id: variantId,
        quantity,
      }),
    },
  );

  if (!response.ok) {
    let detail = `Cart request failed: ${response.status}`;

    try {
      const payload = (await response.json()) as {
        detail?: string;
      };

      if (
        typeof payload.detail === "string"
      ) {
        detail = payload.detail;
      }
    } catch {
      // Use generic detail.
    }

    throw new Error(detail);
  }

  return response.json() as Promise<Cart>;
}

export async function removeCartItem(
  itemId: string,
): Promise<Cart> {
  const csrfToken = await getCsrfToken();

  const response = await fetch(
    `/api/cart/items/${encodeURIComponent(itemId)}`,
    {
      method: "DELETE",
      credentials: "include",
      cache: "no-store",
      headers: {
        "X-CSRF-Token": csrfToken,
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      `Cart request failed: ${response.status}`,
    );
  }

  return response.json() as Promise<Cart>;
}
