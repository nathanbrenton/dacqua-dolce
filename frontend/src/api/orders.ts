import type { CommercialAddress, CommercialCharge } from "./commercial";

export type OrderItem = {
  sku: string;
  name: string;
  quantity: number;
  unit_amount_minor: number;
  line_total_minor: number;
  currency: string;
  estimated_lead_time: string | null;
};

export type OrderShipment = {
  carrier: string;
  tracking_number: string;
  tracking_url: string | null;
  shipped_at: string | null;
  delivered_at: string | null;
};

export type Order = {
  id: string;
  formal_quote_id: string | null;
  status: string;
  fulfillment_status: string;
  subtotal_amount_minor: number;
  charges_amount_minor: number;
  total_amount_minor: number;
  currency: string;
  delivery_address: CommercialAddress | null;
  billing_address: CommercialAddress | null;
  charges: CommercialCharge[];
  created_at: string;
  items: OrderItem[];
  shipment: OrderShipment | null;
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
