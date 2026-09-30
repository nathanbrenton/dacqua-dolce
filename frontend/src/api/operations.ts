import {
  getCsrfToken,
} from "./authentication";

import type {
  RecommendationDecision,
} from "./quotes";

export type OperationsSummary = {
  new_quotes: number;
  open_quotes: number;
  recommendation_human_review: number;
  recommendation_lab_testing: number;
  active_products: number;
  failed_email_deliveries: number;
};

export type OperationsInsightBucket = {
  value: string;
  count: number;
};

export type OperationsSalesInsights = {
  total_requests: number;
  structured_requests: number;
  source_water: OperationsInsightBucket[];
  treatment_preference: OperationsInsightBucket[];
  service_postal_codes: OperationsInsightBucket[];
  limited_utility_requests: number;
  lab_required_requests: number;
  known_hardness_requests: number;
  research_network_yes: number;
};

export type OperationsAuditEvent = {
  id: string;
  actor_user_id: string | null;
  actor_email: string | null;
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

export type OperationsCommunicationRecipient = {
  recipient_type: string;
  address: string;
  display_name: string | null;
};

export type OperationsCommunicationAttachment = {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  sha256: string;
};

export type OperationsCommunicationMessage = {
  id: string;
  direction: string;
  status: string;
  author_user_id: string | null;
  sender_address: string;
  sender_name: string | null;
  subject: string;
  body_text: string | null;
  content_redacted: boolean;
  sent_at: string | null;
  received_at: string | null;
  created_at: string;
  recipients: OperationsCommunicationRecipient[];
  attachments: OperationsCommunicationAttachment[];
};

export type OperationsCommunicationThread = {
  id: string;
  customer_user_id: string | null;
  customer_email: string | null;
  assigned_user_id: string | null;
  subject: string | null;
  related_entity_type: string | null;
  related_entity_id: string | null;
  status: string;
  last_message_at: string | null;
  created_at: string;
  message_count: number;
  latest_direction: string | null;
  latest_sender_address: string | null;
  latest_subject: string | null;
  failed_message_count: number;
  mailbox_kind: "inbox" | "system";
};

export type OperationsCommunicationOriginatingRequest = {
  request_type: string;
  name: string;
  email: string;
  phone: string | null;
  product_name: string | null;
  message: string | null;
  created_at: string;
};

export type OperationsCommunicationThreadDetail =
  OperationsCommunicationThread & {
    reply_target: string | null;
    reply_target_source: string | null;
    reply_sender_addresses: string[];
    reply_sender_default: string | null;
    originating_request: OperationsCommunicationOriginatingRequest | null;
    messages: OperationsCommunicationMessage[];
  };

export type OperationsCommunicationReply = {
  delivery_status: string;
  recipient: string;
  recipients: string[];
  sender: string;
  thread: OperationsCommunicationThreadDetail;
};

export type OperationsFormalQuoteItem = {
  id: string;
  product_id: string | null;
  variant_id: string | null;
  sku: string;
  name: string;
  quantity: number;
  unit_amount_minor: number;
  line_total_minor: number;
  currency: string;
  pricing_policy_mode: string;
  estimated_lead_time: string | null;
};

export type OperationsFormalQuote = {
  id: string;
  revision_number: number;
  status: "draft" | "presented" | "approved" | "superseded";
  customer_user_id: string | null;
  authored_by_user_id: string | null;
  currency: string;
  subtotal_amount_minor: number;
  customer_note: string | null;
  presented_at: string | null;
  approved_at: string | null;
  created_at: string;
  items: OperationsFormalQuoteItem[];
};

export type OperationsQuote = {
  id: string;
  product_id: string | null;
  product_name: string | null;
  name: string;
  email: string;
  phone: string | null;
  message: string | null;
  recommendation_context: Record<string, unknown> | null;
  recommendation_decision: RecommendationDecision | null;
  recommendation_policy_version: string | null;
  internal_notes: string | null;
  status: string;
  created_at: string;
  formal_quotes: OperationsFormalQuote[];
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

export type OperationsCustomerEquipment = {
  id: string;
  product_id: string | null;
  variant_id: string | null;
  sku: string;
  product_name: string;
  variant_name: string | null;
  serial_number: string | null;
  location_label: string | null;
  installed_on: string | null;
  last_service_on: string | null;
  next_service_due_on: string | null;
  active: boolean;
};


export type OperationsCustomer = {
  id: string;
  email: string;
  status: string;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  addresses: OperationsCustomerAddress[];
  equipment: OperationsCustomerEquipment[];
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
  estimated_lead_time: string | null;
};

export type OperationsOrderShipment = {
  carrier: string;
  tracking_number: string;
  tracking_url: string | null;
  shipped_at: string | null;
  delivered_at: string | null;
};

export type OperationsOrder = {
  id: string;
  status: string;
  fulfillment_status: string;
  supplier_order_reference: string | null;
  supplier_ordered_at: string | null;
  received_ready_at: string | null;
  shipped_at: string | null;
  delivered_at: string | null;
  total_amount_minor: number;
  currency: string;
  created_at: string;
  customer: OperationsOrderCustomer;
  items: OperationsOrderItem[];
  shipment: OperationsOrderShipment | null;
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
  estimated_lead_time: string | null;
  source_kind:
    | "unspecified"
    | "operator_entry"
    | "supplier_report"
    | "manufacturer_report"
    | "internal_stock";
  source_reference: string | null;
  source_observed_at: string | null;
};

export type OperationsProductVariant = {
  id: string;
  sku: string;
  display_name: string;
  option_values: Record<string, string>;
};


export type OperationsProductRelationship = {
  id: string;
  related_product_id: string;
  related_sku: string;
  related_name: string;
  relationship_type: "option" | "accessory";
  public: boolean;
  active: boolean;
  is_consumable: boolean;
  replacement_interval_days: number | null;
  reminder_preference:
    | "filter_replacement"
    | "uv_service"
    | "product_specific"
    | null;
  sort_order: number;
};

export type OperationsProduct = {
  id: string;
  sku: string;
  name: string;
  category: string;
  manufacturer: string;
  product_family: string | null;
  system_type: string | null;
  active_variant_count: number;
  variants: OperationsProductVariant[];
  public_option_count: number;
  relationships: OperationsProductRelationship[];
  active: boolean;
  online_sale_approved: boolean;
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
  method: "PATCH" | "POST" | "PUT",
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

export function getOperationsSalesInsights(): Promise<OperationsSalesInsights> {
  return getJson(
    "/api/operations/sales-insights",
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

export function getOperationsCommunicationThreads(): Promise<
  OperationsCommunicationThread[]
> {
  return getJson(
    "/api/operations/communication-threads",
  );
}

export function getOperationsCommunicationThread(
  threadId: string,
): Promise<OperationsCommunicationThreadDetail> {
  return getJson(
    `/api/operations/communication-threads/${encodeURIComponent(threadId)}`,
  );
}


export function updateOperationsCommunicationThreadStatus(
  threadId: string,
  status: "open" | "closed",
): Promise<OperationsCommunicationThread> {
  return writeJson(
    `/api/operations/communication-threads/${encodeURIComponent(threadId)}`,
    "PATCH",
    { status },
  );
}

export function replyToOperationsCommunicationThread(
  threadId: string,
  bodyText: string,
  recipient: string,
  sender: string,
): Promise<OperationsCommunicationReply> {
  return writeJson(
    `/api/operations/communication-threads/${encodeURIComponent(threadId)}/reply`,
    "POST",
    {
      body_text: bodyText,
      recipient,
      sender,
    },
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


export function createFormalQuote(
  quoteId: string,
  payload: {
    items: Array<{
      product_id: string;
      variant_id: string | null;
      quantity: number;
      unit_amount_minor: number | null;
    }>;
    customer_note: string | null;
  },
): Promise<OperationsFormalQuote> {
  return writeJson(
    `/api/operations/quotes/${encodeURIComponent(quoteId)}/formal-quotes`,
    "POST",
    payload,
  );
}

export function presentFormalQuote(
  formalQuoteId: string,
): Promise<OperationsFormalQuote> {
  return writeJson(
    `/api/operations/formal-quotes/${encodeURIComponent(formalQuoteId)}/present`,
    "POST",
    {},
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

export function updateOrderFulfillment(
  orderId: string,
  payload: {
    status: string;
    supplier_order_reference?: string | null;
    carrier?: string | null;
    tracking_number?: string | null;
    tracking_url?: string | null;
  },
): Promise<OperationsOrder> {
  return writeJson(
    `/api/operations/orders/${encodeURIComponent(orderId)}/fulfillment`,
    "POST",
    payload,
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
    estimated_lead_time: string | null;
    source_kind: OperationsInventory["source_kind"];
    source_reference: string | null;
  },
): Promise<OperationsProduct> {
  return writeJson(
    `/api/operations/products/${encodeURIComponent(productId)}/inventory`,
    "PUT",
    payload,
  );
}

export function createProductRelationship(
  productId: string,
  payload: {
    related_product_id: string;
    relationship_type: "option" | "accessory";
    public: boolean;
    active: boolean;
    is_consumable: boolean;
    replacement_interval_days: number | null;
    reminder_preference:
      | "filter_replacement"
      | "uv_service"
      | "product_specific"
      | null;
    sort_order: number;
  },
): Promise<OperationsProduct> {
  return writeJson(
    `/api/operations/products/${encodeURIComponent(productId)}/relationships`,
    "POST",
    payload,
  );
}

export function updateProductRelationship(
  productId: string,
  relationshipId: string,
  payload: {
    relationship_type: "option" | "accessory";
    public: boolean;
    active: boolean;
    is_consumable: boolean;
    replacement_interval_days: number | null;
    reminder_preference:
      | "filter_replacement"
      | "uv_service"
      | "product_specific"
      | null;
    sort_order: number;
  },
): Promise<OperationsProduct> {
  return writeJson(
    `/api/operations/products/${encodeURIComponent(productId)}/relationships/${encodeURIComponent(relationshipId)}`,
    "PUT",
    payload,
  );
}

export async function deleteProductRelationship(
  productId: string,
  relationshipId: string,
): Promise<OperationsProduct> {
  const csrfToken = await getCsrfToken();
  const response = await fetch(
    `/api/operations/products/${encodeURIComponent(productId)}/relationships/${encodeURIComponent(relationshipId)}`,
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
    throw new Error(await readError(response));
  }

  return response.json() as Promise<OperationsProduct>;
}


export function createCustomerEquipment(
  customerId: string,
  payload: {
    product_id: string;
    variant_id: string | null;
    serial_number: string | null;
    location_label: string | null;
    installed_on: string | null;
    last_service_on: string | null;
    next_service_due_on: string | null;
  },
): Promise<OperationsCustomer> {
  return writeJson(
    `/api/operations/customers/${encodeURIComponent(customerId)}/equipment`,
    "POST",
    payload,
  );
}

export function updateCustomerEquipment(
  customerId: string,
  equipmentId: string,
  payload: {
    serial_number: string | null;
    location_label: string | null;
    installed_on: string | null;
    last_service_on: string | null;
    next_service_due_on: string | null;
    active: boolean;
  },
): Promise<OperationsCustomer> {
  return writeJson(
    `/api/operations/customers/${encodeURIComponent(customerId)}/equipment/${encodeURIComponent(equipmentId)}`,
    "PATCH",
    payload,
  );
}
