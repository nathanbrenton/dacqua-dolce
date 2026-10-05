import { getCsrfToken } from "./authentication";
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

export type OrderCancellation = {
  id: string;
  eligibility_mode: "unrestricted" | "manual_review";
  status: "requested" | "approved" | "declined" | "completed";
  reason: string | null;
  requested_at: string;
  reviewed_at: string | null;
  completed_at: string | null;
};


export type Order = {
  id: string;
  formal_quote_id: string | null;
  status: string;
  fulfillment_status: string;
  customer_status:
    | "received"
    | "processing"
    | "supplier_confirmed"
    | "awaiting_shipment"
    | "shipped"
    | "completed"
    | "cancelled"
    | "refunded";
  cancellation_mode:
    | "unrestricted"
    | "closed_after_supplier_confirmation";
  cancellation: OrderCancellation | null;
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

async function readError(response: Response): Promise<string> {
  try {
    const payload = await response.json() as { detail?: string };
    return payload.detail ?? `Request failed: ${response.status}`;
  } catch {
    return `Request failed: ${response.status}`;
  }
}

export async function requestOrderCancellation(
  orderId: string,
  reason: string | null,
): Promise<OrderCancellation> {
  const csrfToken = await getCsrfToken();
  const response = await fetch(
    `/api/orders/${encodeURIComponent(orderId)}/cancellation`,
    {
      method: "POST",
      credentials: "include",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({ reason }),
    },
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<OrderCancellation>;
}
