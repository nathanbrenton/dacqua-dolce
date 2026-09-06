export type OrderItem = {
  sku: string;
  name: string;
  quantity: number;
  unit_amount_minor: number;
  line_total_minor: number;
  currency: string;
};

export type Order = {
  id: string;
  status: string;
  total_amount_minor: number;
  currency: string;
  created_at: string;
  items: OrderItem[];
};

export async function getOrders(): Promise<Order[]> {
  const response = await fetch(
    "/api/orders",
    {
      credentials: "include",
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Orders request failed: ${response.status}`,
    );
  }

  return response.json() as Promise<Order[]>;
}
