import { getCsrfToken } from "./authentication";

export type RecommendationContext = {
  source_water: "municipal" | "well" | "unsure";
  hard_water_signs: "yes" | "no" | "unsure";
  bathrooms: "1" | "2" | "3" | "4" | "5+" | "unsure";
  occupants: number | null;
  water_service_pipe_size: string | null;
  water_quality_report_read: "yes" | "no" | "unsure";
  chlorine_chloramine_signs: "yes" | "no" | "unsure";
  iron_manganese_concerns: "yes" | "no" | "unsure";
  existing_equipment: string | null;
  drain_available: "yes" | "no" | "unsure";
  electrical_available: "yes" | "no" | "unsure";
  irrigation_hose_bib: "yes" | "no" | "unsure";
  pool_autofill: "yes" | "no" | "unsure";
  drinking_water_ro: "yes" | "no" | "unsure";
  water_test_results: "yes" | "no" | "unsure";
  water_filtration_network: "yes" | "no" | "unsure";
  treatment_preference: "salt_free" | "softened" | "unsure";
};

export type RecommendationDecision = {
  code:
    | "well_testing_required"
    | "source_water_review"
    | "limited_utilities"
    | "installation_review"
    | "salt_free"
    | "softened_with_ro"
    | "treatment_preference_review";
  title: string;
  description: string;
  human_review: boolean;
  requires_third_party_lab: boolean;
  components: Array<
    | "harmony"
    | "cartridge_filtration"
    | "backwashing_carbon"
    | "water_softener"
    | "reverse_osmosis"
  >;
  sizing?: {
    status: "inputs_complete" | "needs_more_information";
    missing_inputs: Array<
      "bathrooms" | "occupants" | "water_service_pipe_size"
    >;
    capacity_recommendation_available: boolean;
  };
};

export type QuoteRequestPayload = {
  product_id: string | null;
  name: string;
  email: string;
  phone: string | null;
  message: string | null;
  recommendation_context: RecommendationContext | null;
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


export async function evaluateRecommendation(
  payload: RecommendationContext,
  signal?: AbortSignal,
): Promise<RecommendationDecision> {
  const csrfToken = await getCsrfToken();

  const response = await fetch(
    "/api/quotes/recommendation",
    {
      method: "POST",
      credentials: "include",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify(payload),
      signal,
    },
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<RecommendationDecision>;
}
