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

export type PolicySnapshot = {
  id: string;
  kind: PolicyKind;
  version: string;
  title: string;
  body: string;
  content_sha256: string;
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
