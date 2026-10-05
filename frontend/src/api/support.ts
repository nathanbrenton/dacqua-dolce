import { getCsrfToken } from "./authentication";

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
};

export type SupportRequestResponse = {
  id: string;
  status: "received";
  message: string;
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
  return `Support request failed: ${response.status}`;
}

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
    throw new Error(await readError(response));
  }

  return response.json() as Promise<SupportRequestResponse>;
}
