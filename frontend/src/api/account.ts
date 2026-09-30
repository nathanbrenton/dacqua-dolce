import { getCsrfToken } from "./authentication";

import type { CommercialAddress, CommercialCharge } from "./commercial";

export type CustomerAddress = {
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

export type CustomerProfile = {
  email: string;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  addresses: CustomerAddress[];
};

export type CustomerProfileUpdate = {
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
};

export type AddressCreate = Omit<
  CustomerAddress,
  "id"
>;

export type CommunicationPreferences = {
  filter_replacement_reminders: boolean;
  softener_check_reminders: boolean;
  uv_service_reminders: boolean;
  annual_system_check_reminders: boolean;
  product_specific_reminders: boolean;
  post_purchase_followup: boolean;
  post_installation_followup: boolean;
};

export type CustomerEquipmentDocument = {
  title: string;
  document_type: string;
  path: string;
  content_type: string;
  version: string;
};

export type CustomerConsumable = {
  product_id: string;
  name: string;
  sku: string;
  public_path: string;
  replacement_interval_days: number | null;
  next_replacement_due_on: string | null;
  calendar_path: string | null;
  online_reorder_available: boolean;
};

export type CustomerEquipment = {
  id: string;
  product_id: string | null;
  product_name: string;
  product_family: string | null;
  system_type: string | null;
  sku: string;
  variant_name: string | null;
  serial_number: string | null;
  location_label: string | null;
  installed_on: string | null;
  last_service_on: string | null;
  next_service_due_on: string | null;
  service_calendar_path: string | null;
  consumables: CustomerConsumable[];
  documents: CustomerEquipmentDocument[];
};


export type CustomerFormalQuoteItem = {
  sku: string;
  name: string;
  quantity: number;
  unit_amount_minor: number;
  line_total_minor: number;
  currency: string;
  estimated_lead_time: string | null;
};

export type CustomerFormalQuotePolicySnapshot = {
  id: string;
  kind: string;
  version: string;
  title: string;
  body: string;
  content_sha256: string;
  effective_at: string | null;
};

export type CustomerFormalQuote = {
  id: string;
  request_id: string;
  revision_number: number;
  status: "presented" | "approved" | "superseded";
  currency: string;
  subtotal_amount_minor: number;
  charges_amount_minor: number;
  total_amount_minor: number;
  delivery_address: CommercialAddress | null;
  billing_address: CommercialAddress | null;
  charges: CommercialCharge[];
  policy_snapshots: CustomerFormalQuotePolicySnapshot[];
  customer_note: string | null;
  presented_at: string | null;
  approved_at: string | null;
  created_at: string;
  items: CustomerFormalQuoteItem[];
};

export type CustomerRequestSummary = {
  id: string;
  status: string;
  product_name: string | null;
  created_at: string;
  recommendation_title: string | null;
  human_review: boolean;
  requires_third_party_lab: boolean;
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

  return `Account request failed: ${response.status}`;
}

export async function getProfile(): Promise<CustomerProfile> {
  const response = await fetch(
    "/api/account/profile",
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

  return response.json() as Promise<CustomerProfile>;
}

export async function updateProfile(
  payload: CustomerProfileUpdate,
): Promise<CustomerProfile> {
  const csrfToken = await getCsrfToken();

  const response = await fetch(
    "/api/account/profile",
    {
      method: "PUT",
      credentials: "include",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify(payload),
    },
  );

  if (!response.ok) {
    throw new Error(
      await readError(response),
    );
  }

  return response.json() as Promise<CustomerProfile>;
}

export async function createAddress(
  payload: AddressCreate,
): Promise<CustomerAddress> {
  const csrfToken = await getCsrfToken();

  const response = await fetch(
    "/api/account/addresses",
    {
      method: "POST",
      credentials: "include",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify(payload),
    },
  );

  if (!response.ok) {
    throw new Error(
      await readError(response),
    );
  }

  return response.json() as Promise<CustomerAddress>;
}

export async function deleteAddress(
  id: string,
): Promise<void> {
  const csrfToken = await getCsrfToken();

  const response = await fetch(
    `/api/account/addresses/${encodeURIComponent(id)}`,
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
      await readError(response),
    );
  }
}


export async function getCommunicationPreferences(): Promise<CommunicationPreferences> {
  const response = await fetch(
    "/api/account/communication-preferences",
    { credentials: "include", cache: "no-store" },
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<CommunicationPreferences>;
}

export async function updateCommunicationPreferences(
  payload: CommunicationPreferences,
): Promise<CommunicationPreferences> {
  const csrfToken = await getCsrfToken();
  const response = await fetch(
    "/api/account/communication-preferences",
    {
      method: "PUT",
      credentials: "include",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify(payload),
    },
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<CommunicationPreferences>;
}

export async function getCustomerRequests(): Promise<CustomerRequestSummary[]> {
  const response = await fetch(
    "/api/account/requests",
    { credentials: "include", cache: "no-store" },
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<CustomerRequestSummary[]>;
}


export async function getCustomerEquipment(): Promise<CustomerEquipment[]> {
  const response = await fetch(
    "/api/account/equipment",
    { credentials: "include", cache: "no-store" },
  );
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json() as Promise<CustomerEquipment[]>;
}

export async function getCustomerFormalQuotes(): Promise<CustomerFormalQuote[]> {
  const response = await fetch(
    "/api/account/quotes",
    { credentials: "include", cache: "no-store" },
  );
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json() as Promise<CustomerFormalQuote[]>;
}

export async function approveCustomerFormalQuote(
  quoteId: string,
  policySnapshotIds: string[],
): Promise<CustomerFormalQuote> {
  const csrfToken = await getCsrfToken();
  const response = await fetch(
    `/api/account/quotes/${encodeURIComponent(quoteId)}/approve`,
    {
      method: "POST",
      credentials: "include",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({
        policy_snapshot_ids: policySnapshotIds,
      }),
    },
  );
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json() as Promise<CustomerFormalQuote>;
}
