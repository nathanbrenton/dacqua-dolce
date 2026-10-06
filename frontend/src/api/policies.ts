import {
  getCsrfToken,
} from "./authentication";

export type PolicyKind =
  | "privacy"
  | "terms"
  | "shipping"
  | "cancellation"
  | "refund"
  | "warranty"
  | "installation";

export type PolicyDocumentStatus =
  | "draft"
  | "approved"
  | "retired";

export type RefundPolicyTerms = {
  eligibility_mode:
    | "fixed_window"
    | "case_by_case"
    | "fixed_window_with_exception";
  return_window_days: number | null;
  restocking_mode:
    | "fixed_percentage"
    | "case_by_case";
  restocking_fee_basis_points: number | null;
  merchandise_condition: "new_uninstalled";
  customer_pays_return_shipping_by_default: boolean;
  outbound_shipping_refund_rule:
    "nonrefundable_with_error_defect_or_discretion_exception";
  acknowledgement_required: boolean;
};

export type PolicySnapshot = {
  id: string;
  kind: PolicyKind;
  version: string;
  title: string;
  body: string;
  refund_terms: RefundPolicyTerms | null;
  content_sha256: string;
  structured_terms_sha256: string | null;
  effective_at: string | null;
};

export type PublicPolicy = {
  kind: PolicyKind;
  approved: boolean;
  title: string;
  version: string | null;
  body: string | null;
  effective_at: string | null;
};

export type PolicyDocument = {
  id: string;
  kind: PolicyKind;
  version: string;
  title: string;
  body: string;
  refund_terms: RefundPolicyTerms | null;
  status: PolicyDocumentStatus;
  effective_at: string | null;
  approved_at: string | null;
  approved_by_user_id: string | null;
  created_by_user_id: string | null;
  created_at: string;
};

async function readError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string };
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
  } catch {
    // Fall through.
  }
  return `Policy request failed: ${response.status}`;
}

export async function getPublicPolicy(kind: PolicyKind): Promise<PublicPolicy> {
  const response = await fetch(
    `/api/policies/${encodeURIComponent(kind)}`,
    { credentials: "include", cache: "no-store" },
  );
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json() as Promise<PublicPolicy>;
}

export async function getOperationsPolicies(): Promise<PolicyDocument[]> {
  const response = await fetch(
    "/api/operations/policies",
    { credentials: "include", cache: "no-store" },
  );
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json() as Promise<PolicyDocument[]>;
}

export async function createPolicyDraft(payload: {
  kind: PolicyKind;
  version: string;
  title: string;
  body: string;
  refund_terms?: RefundPolicyTerms | null;
}): Promise<PolicyDocument> {
  const csrfToken = await getCsrfToken();
  const response = await fetch(
    "/api/operations/policies",
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
    throw new Error(await readError(response));
  }
  return response.json() as Promise<PolicyDocument>;
}

export async function approvePolicyDocument(
  policyId: string,
): Promise<PolicyDocument> {
  const csrfToken = await getCsrfToken();
  const response = await fetch(
    `/api/operations/policies/${encodeURIComponent(policyId)}/approve`,
    {
      method: "POST",
      credentials: "include",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: "{}",
    },
  );
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json() as Promise<PolicyDocument>;
}

export type PolicyExportScope = "all" | "approved_effective";
export type PolicyImportMode = "draft_only" | "preserve_lifecycle";

export type PolicyExportEntry = {
  kind: PolicyKind;
  version: string;
  title: string;
  body: string;
  structured_terms: Record<string, unknown> | null;
  status: PolicyDocumentStatus;
  effective_at: string | null;
  approved_at: string | null;
  source_created_at: string;
  content_sha256: string;
  structured_terms_sha256: string | null;
};

export type PolicyExportBundle = {
  format: string;
  format_version: number;
  scope: PolicyExportScope;
  exported_at: string;
  policies: PolicyExportEntry[];
  bundle_sha256: string;
};

export type PolicyImportAction = {
  kind: PolicyKind;
  version: string;
  action:
    | "add"
    | "skip"
    | "conflict"
    | "update_lifecycle"
    | "retire_destination_approved";
  detail: string;
};

export type PolicyImportReport = {
  mode: PolicyImportMode;
  source_scope: PolicyExportScope;
  bundle_sha256: string;
  lifecycle_preservation_allowed: boolean;
  additions: number;
  skips: number;
  conflicts: number;
  lifecycle_updates: number;
  destination_retirements: number;
  actions: PolicyImportAction[];
};

export async function exportPolicyBundle(
  scope: PolicyExportScope,
): Promise<PolicyExportBundle> {
  const response = await fetch(
    `/api/operations/policies/export?scope=${encodeURIComponent(scope)}`,
    { credentials: "include", cache: "no-store" },
  );
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json() as Promise<PolicyExportBundle>;
}

async function postPolicyImport(
  path: "preview" | "apply",
  bundle: PolicyExportBundle,
  mode: PolicyImportMode,
): Promise<PolicyImportReport> {
  const csrfToken = await getCsrfToken();
  const response = await fetch(
    `/api/operations/policies/import/${path}`,
    {
      method: "POST",
      credentials: "include",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({ bundle, mode }),
    },
  );
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json() as Promise<PolicyImportReport>;
}

export async function previewPolicyImport(
  bundle: PolicyExportBundle,
  mode: PolicyImportMode,
): Promise<PolicyImportReport> {
  return postPolicyImport("preview", bundle, mode);
}

export async function applyPolicyImport(
  bundle: PolicyExportBundle,
  mode: PolicyImportMode,
): Promise<PolicyImportReport> {
  return postPolicyImport("apply", bundle, mode);
}
