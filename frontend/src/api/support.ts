import { getCsrfToken } from "./authentication";
import { readApiError } from "./httpErrors";

export type SupportRequestKind =
  | "warranty"
  | "product_support"
  | "general_support";

export type SupportRequestPayload = {
  kind: SupportRequestKind;
  name: string;
  email: string;
  phone: string | null;
  product_id: string | null;
  message: string;
  website: string | null;
};

export type SupportRequestResponse = {
  id: string;
  status: "received";
  message: string;
};

export async function submitSupportRequest(
  payload: SupportRequestPayload,
): Promise<SupportRequestResponse> {
  const csrfToken = await getCsrfToken();
  const response = await fetch("/api/support", {
    method: "POST",
    credentials: "include",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await readApiError(response, "Support request failed"));
  }

  return response.json() as Promise<SupportRequestResponse>;
}
