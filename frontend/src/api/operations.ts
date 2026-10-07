import {
  getCsrfToken,
} from "./authentication";

import type {
  CommercialAddress,
  CommercialCharge,
  CommercialChargeKind,
  CommercialCostBreakdown,
} from "./commercial";
import type {
  RecommendationDecision,
} from "./quotes";
import type {
  PolicySnapshot,
} from "./policies";

export type OperationsSummary = {
  new_quotes: number;
  open_quotes: number;
  recommendation_human_review: number;
  recommendation_lab_testing: number;
  active_products: number;
  failed_email_deliveries: number;
};

export type LaunchReadinessStatus =
  | "ready"
  | "action_required"
  | "deferred";

export type OperationsLaunchReadinessCheck = {
  key: string;
  label: string;
  status: LaunchReadinessStatus;
  detail: string;
  evidence: string[];
};

export type OperationsLaunchReadiness = {
  status: LaunchReadinessStatus;
  ready_count: number;
  action_required_count: number;
  deferred_count: number;
  launch_phase:
    | "prelaunch"
    | "soft_launch"
    | "public_launch"
    | "invalid";
  launch_phase_label: string;
  commerce_checkout_allowed: boolean;
  commerce_gate_detail: string;
  commerce_blockers: string[];
  evaluated_at: string;
  checks: OperationsLaunchReadinessCheck[];
};

export type LaunchDependencyKey =
  | "tax"
  | "payment_checkout"
  | "legal_review"
  | "shipping_insurance"
  | "support_phone"
  | "installer_program";

export type LaunchDependencyTrackingStatus =
  | "action_required"
  | "in_progress"
  | "evidence_received"
  | "verified"
  | "blocked";

export type OperationsLaunchDependencyEvidence = {
  dependency_key: LaunchDependencyKey;
  label: string;
  tracking_status: LaunchDependencyTrackingStatus;
  source_reference: string | null;
  evidence_received_at: string | null;
  internal_notes: string | null;
  created_by_user_id: string | null;
  updated_by_user_id: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type LaunchDependencyEvidenceInput = {
  tracking_status: LaunchDependencyTrackingStatus;
  source_reference: string | null;
  evidence_received_at: string | null;
  internal_notes: string | null;
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
  outcome: "succeeded" | "failed";
  request_id: string | null;
  error_category: string | null;
  endpoint: string | null;
  error_code: string | null;
  created_at: string;
};

export type OperationsAuditEventPage = {
  items: OperationsAuditEvent[];
  page: number;
  page_size: number;
  has_more: boolean;
};

export type OperationsAuditEventQuery = {
  from?: string;
  to?: string;
  actor?: string;
  outcome?: "succeeded" | "failed";
  action?: string;
  entity_type?: string;
  entity_id?: string;
  environment?: string;
  request_id?: string;
  search?: string;
  sort?: "newest" | "oldest";
  page?: number;
  page_size?: number;
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
  requires_review: boolean;
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

export type OperationsCommunicationSecurity = {
  spam_status: string | null;
  spam_score: number | null;
  spam_tests: string[];
  spf_result: string | null;
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
  security?: OperationsCommunicationSecurity | null;
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

export type InstallerCandidateStatus =
  | "researching"
  | "contacted"
  | "review_pending"
  | "inactive";

export type OperationsInstallerCandidate = {
  id: string;
  business_name: string;
  contact_name: string | null;
  email: string | null;
  phone: string | null;
  website: string | null;
  service_area_notes: string | null;
  source_reference: string | null;
  status: InstallerCandidateStatus;
  internal_notes: string | null;
  created_by_user_id: string;
  updated_by_user_id: string;
  created_at: string;
  updated_at: string;
};

export type InstallerCandidateInput = {
  business_name: string;
  contact_name: string | null;
  email: string | null;
  phone: string | null;
  website: string | null;
  service_area_notes: string | null;
  source_reference: string | null;
  status: InstallerCandidateStatus;
  internal_notes: string | null;
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

export type OperationsWarrantySnapshot = {
  id: string;
  sku: string;
  product_name: string;
  manufacturer_name: string;
  title: string;
  version: string;
  path: string;
  content_type: string;
  checksum_sha256: string;
  source_reference: string | null;
  verified_at: string;
};

export type OperationsFormalQuote = {
  id: string;
  revision_number: number;
  status: "draft" | "presented" | "approved" | "superseded";
  customer_user_id: string | null;
  authored_by_user_id: string | null;
  currency: string;
  subtotal_amount_minor: number;
  charges_amount_minor: number;
  total_amount_minor: number;
  cost_breakdown: CommercialCostBreakdown;
  delivery_address: CommercialAddress | null;
  billing_address: CommercialAddress | null;
  charges: CommercialCharge[];
  policy_snapshots: PolicySnapshot[];
  warranty_snapshots: OperationsWarrantySnapshot[];
  shipping_insurance_offered: boolean;
  shipping_insurance_decision: "accepted" | "declined" | null;
  shipping_insurance_decided_at: string | null;
  shipping_insurance_decided_by_user_id: string | null;
  customer_note: string | null;
  staff_review_required: boolean;
  staff_review_reasons: string[];
  staff_review_completed_at: string | null;
  staff_review_completed_by_user_id: string | null;
  presented_at: string | null;
  expires_at: string | null;
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

export type OperationsOrderCancellation = {
  id: string;
  eligibility_mode: "unrestricted" | "manual_review";
  status: "requested" | "approved" | "declined" | "completed";
  reason: string | null;
  review_note: string | null;
  requested_at: string;
  reviewed_at: string | null;
  completed_at: string | null;
};


export type OperationsReturnPolicyException = {
  id: string;
  actor_user_id: string | null;
  created_at: string;
  policy_snapshot_id: string;
  policy_version: string;
  reason: string;
  return_window_days_override: number | null;
  restocking_fee_basis_points_override: number | null;
  customer_pays_return_shipping_override: boolean | null;
  refund_outbound_shipping_override: boolean | null;
};


export type OperationsOrder = {
  id: string;
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
  cancellation: OperationsOrderCancellation | null;
  review: {
    status: "pending" | "reviewed";
    customer_contact_reviewed: boolean;
    supplier_availability_verified: boolean;
    whole_order_reviewed: boolean;
    customer_contact_required: boolean;
    customer_contact_completed: boolean;
    reviewed_by_user_id: string | null;
    reviewed_by_email: string | null;
    reviewed_at: string | null;
    on_hold: boolean;
    hold_reason: string | null;
    proposed_alternative: string | null;
    hold_started_by_user_id: string | null;
    hold_started_at: string | null;
    hold_released_by_user_id: string | null;
    hold_released_at: string | null;
    customer_response_note: string | null;
  };
  order_confirmation: {
    delivery_id: string | null;
    status: "not_sent" | "pending" | "sent" | "suppressed" | "failed";
    attempted_at: string | null;
    sent_at: string | null;
    error_summary: string | null;
  };
  refund_policy_snapshot: PolicySnapshot | null;
  return_policy_exceptions: OperationsReturnPolicyException[];
  supplier_order_reference: string | null;
  supplier_ordered_at: string | null;
  received_ready_at: string | null;
  shipped_at: string | null;
  delivered_at: string | null;
  subtotal_amount_minor: number;
  charges_amount_minor: number;
  total_amount_minor: number;
  currency: string;
  delivery_address: CommercialAddress | null;
  billing_address: CommercialAddress | null;
  charges: CommercialCharge[];
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
  effective_until: string | null;
};

export type OperationsPromotion = {
  id: string;
  mode: string;
  amount_minor: number;
  currency: string;
  effective_from: string;
  effective_until: string;
  state: "scheduled" | "active";
};

export type OperationsInventory = {
  status: string;
  quantity_on_hand: number;
  quantity_reserved: number;
  expected_available_on: string | null;
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

export type OperationsStockNotification = {
  id: string;
  product_id: string;
  product_sku: string;
  product_name: string;
  email: string;
  active: boolean;
  notified_at: string | null;
  created_at: string;
  updated_at: string;
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
  relationship_type: "option" | "accessory" | "replacement";
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

export type OperationsWarrantyDocument = {
  id: string;
  title: string;
  version: string;
  path: string;
  content_type: string;
  checksum_sha256: string | null;
  source_reference: string | null;
  public: boolean;
  active: boolean;
  verified_at: string | null;
};

export type OperationsProductSpecification = {
  id: string;
  spec_key: string;
  label: string;
  value_text: string;
  unit: string | null;
  source_reference: string;
  public: boolean;
  active: boolean;
  verified_at: string | null;
};

export type OperationsManufacturerClaim = {
  id: string;
  claim_text: string;
  source_reference: string;
  approved_by: string | null;
  approved_at: string | null;
  expires_at: string | null;
  active: boolean;
  public_ready: boolean;
};

export type OperationsTaxClassification = {
  provider: string;
  tax_code: string;
  source_reference: string;
  verified_at: string;
  verified_by_user_id: string | null;
  active: boolean;
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
  assisted_sale_required: boolean;
  online_sale_approved: boolean;
  lifecycle_status: "active" | "soon_discontinued" | "discontinued";
  public_retire_at: string | null;
  public_catalog_visible: boolean;
  allow_inquiry_when_unavailable: boolean;
  allow_formal_quote_when_unavailable: boolean;
  warranty_documents: OperationsWarrantyDocument[];
  specifications: OperationsProductSpecification[];
  manufacturer_claims: OperationsManufacturerClaim[];
  tax_classification: OperationsTaxClassification | null;
  pricing: OperationsPricing;
  standard_pricing: OperationsPricing;
  promotions: OperationsPromotion[];
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

export function getOperationsLaunchReadiness(): Promise<
  OperationsLaunchReadiness
> {
  return getJson(
    "/api/operations/launch-readiness",
  );
}

export function getLaunchDependencyEvidence(): Promise<
  OperationsLaunchDependencyEvidence[]
> {
  return getJson(
    "/api/operations/launch-dependency-evidence",
  );
}

export function updateLaunchDependencyEvidence(
  dependencyKey: LaunchDependencyKey,
  payload: LaunchDependencyEvidenceInput,
): Promise<OperationsLaunchDependencyEvidence> {
  return writeJson(
    `/api/operations/launch-dependency-evidence/${encodeURIComponent(dependencyKey)}`,
    "PATCH",
    payload,
  );
}

export function getOperationsSalesInsights(): Promise<OperationsSalesInsights> {
  return getJson(
    "/api/operations/sales-insights",
  );
}

export function getOperationsAuditEvents(
  query: OperationsAuditEventQuery = {},
): Promise<OperationsAuditEventPage> {
  const params = new URLSearchParams();

  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === "") {
      continue;
    }

    params.set(key, String(value));
  }

  const suffix = params.toString();

  return getJson(
    `/api/operations/audit-events${suffix ? `?${suffix}` : ""}`,
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
    charges: Array<{
      kind: CommercialChargeKind;
      label: string;
      amount_minor: number;
    }>;
    delivery_address: CommercialAddress;
    billing_address: CommercialAddress;
    customer_note: string | null;
    manual_staff_review_required: boolean;
  },
): Promise<OperationsFormalQuote> {
  return writeJson(
    `/api/operations/quotes/${encodeURIComponent(quoteId)}/formal-quotes`,
    "POST",
    payload,
  );
}

export function completeFormalQuoteStaffReview(
  formalQuoteId: string,
): Promise<OperationsFormalQuote> {
  return writeJson(
    `/api/operations/formal-quotes/${encodeURIComponent(formalQuoteId)}/staff-review/complete`,
    "POST",
    {},
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

export function getOperationsInstallerCandidates(): Promise<
  OperationsInstallerCandidate[]
> {
  return getJson(
    "/api/operations/installer-candidates",
  );
}

export function createInstallerCandidate(
  payload: InstallerCandidateInput,
): Promise<OperationsInstallerCandidate> {
  return writeJson(
    "/api/operations/installer-candidates",
    "POST",
    payload,
  );
}

export function updateInstallerCandidate(
  candidateId: string,
  payload: InstallerCandidateInput,
): Promise<OperationsInstallerCandidate> {
  return writeJson(
    `/api/operations/installer-candidates/${encodeURIComponent(candidateId)}`,
    "PATCH",
    payload,
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

export function updateOrderReview(
  orderId: string,
  payload: {
    action: "save" | "complete";
    customer_contact_reviewed: boolean;
    supplier_availability_verified: boolean;
    whole_order_reviewed: boolean;
    customer_contact_required: boolean;
    customer_contact_completed: boolean;
  },
): Promise<OperationsOrder> {
  return writeJson(
    `/api/operations/orders/${encodeURIComponent(orderId)}/review`,
    "POST",
    payload,
  );
}

export function holdOrderForCustomerResponse(
  orderId: string,
  payload: { reason: string; proposed_alternative: string },
): Promise<OperationsOrder> {
  return writeJson(
    `/api/operations/orders/${encodeURIComponent(orderId)}/review/hold`,
    "POST",
    payload,
  );
}

export function releaseOrderCustomerResponseHold(
  orderId: string,
  customerResponseNote: string,
): Promise<OperationsOrder> {
  return writeJson(
    `/api/operations/orders/${encodeURIComponent(orderId)}/review/hold/release`,
    "POST",
    { customer_response_note: customerResponseNote },
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

export function sendOrderConfirmation(
  orderId: string,
): Promise<OperationsOrder> {
  return writeJson(
    `/api/operations/orders/${encodeURIComponent(orderId)}/confirmation`,
    "POST",
    {},
  );
}


export function reviewOrderCancellation(
  orderId: string,
  payload: {
    action: "approve" | "decline" | "complete";
    note?: string | null;
  },
): Promise<OperationsOrder> {
  return writeJson(
    `/api/operations/orders/${encodeURIComponent(orderId)}/cancellation`,
    "POST",
    payload,
  );
}


export function startOrderCancellationException(
  orderId: string,
  reason: string,
): Promise<OperationsOrder> {
  return writeJson(
    `/api/operations/orders/${encodeURIComponent(orderId)}/cancellation-exception`,
    "POST",
    { reason },
  );
}


export function authorizeReturnPolicyException(
  orderId: string,
  payload: {
    reason: string;
    return_window_days_override?: number | null;
    restocking_fee_basis_points_override?: number | null;
    customer_pays_return_shipping_override?: boolean | null;
    refund_outbound_shipping_override?: boolean | null;
  },
): Promise<OperationsOrder> {
  return writeJson(
    `/api/operations/orders/${encodeURIComponent(orderId)}/return-policy-exceptions`,
    "POST",
    payload,
  );
}


export function getOperationsCatalog(): Promise<OperationsProduct[]> {
  return getJson(
    "/api/operations/catalog",
  );
}

export function getOperationsStockNotifications(): Promise<
  OperationsStockNotification[]
> {
  return getJson(
    "/api/operations/stock-notifications",
  );
}

export function updateProductTaxClassification(
  productId: string,
  payload: {
    tax_code: string;
    source_reference: string;
  },
): Promise<OperationsProduct> {
  return writeJson(
    `/api/operations/products/${encodeURIComponent(productId)}/tax-classification`,
    "PUT",
    payload,
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

export function scheduleProductPromotion(
  productId: string,
  payload: {
    amount_minor: number;
    effective_from: string;
    effective_until: string;
  },
): Promise<OperationsProduct> {
  return writeJson(
    `/api/operations/products/${encodeURIComponent(productId)}/promotions`,
    "POST",
    payload,
  );
}

export async function cancelProductPromotion(
  productId: string,
  promotionId: string,
): Promise<OperationsProduct> {
  const csrfToken = await getCsrfToken();
  const response = await fetch(
    `/api/operations/products/${encodeURIComponent(productId)}/promotions/${encodeURIComponent(promotionId)}`,
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

export function updateProductAvailabilityPolicy(
  productId: string,
  payload: {
    lifecycle_status: OperationsProduct["lifecycle_status"];
    public_retire_at: string | null;
    allow_inquiry_when_unavailable: boolean;
    allow_formal_quote_when_unavailable: boolean;
  },
): Promise<OperationsProduct> {
  return writeJson(
    `/api/operations/products/${encodeURIComponent(productId)}/availability-policy`,
    "PUT",
    payload,
  );
}

export function updateProductInventory(
  productId: string,
  payload: {
    status: string;
    quantity_on_hand: number;
    expected_available_on: string | null;
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
    relationship_type: "option" | "accessory" | "replacement";
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
    relationship_type: "option" | "accessory" | "replacement";
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
