import { getCsrfToken } from "./authentication";

export type QuoteRequestPayload = {
  product_id: string | null;
  name: string;
  email: string;
  phone: string | null;
  message: string | null;
};

export type QuoteRequestResponse = {
  id: string;
  status: string;
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

  return (
    `Quote request failed: ${response.status}`
  );
}

export async function submitQuoteRequest(
  payload: QuoteRequestPayload,
): Promise<QuoteRequestResponse> {
  const csrfToken = await getCsrfToken();

  const response = await fetch(
    "/api/quotes",
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

  return response.json() as Promise<
    QuoteRequestResponse
  >;
}
