// Request statuses, queue filters and recommendation-context labels shared by
// the Requests workspace (workspaces/RequestsWorkspace.tsx) and its detail
// pane (requests/RequestDetail.tsx).

import { homeSizeLabel } from "../../../api/quotes";

export const QUOTE_STATUSES = [
  "new",
  "contacted",
  "quoted",
  "closed",
] as const;

export const QUOTE_STATUS_LABELS: Record<
  (typeof QUOTE_STATUSES)[number],
  string
> = {
  new: "New",
  contacted: "Contacted",
  quoted: "Quoted",
  closed: "Closed",
};

export type QuoteStatus = (typeof QUOTE_STATUSES)[number];

export const RECOMMENDATION_COMPONENT_LABELS: Record<string, string> = {
  harmony: "Harmony",
  cartridge_filtration: "Cartridge filtration",
  backwashing_carbon: "Backwashing carbon",
  water_softener: "Water softener",
  reverse_osmosis: "Reverse osmosis",
};

export function recommendationContextLabel(key: string): string {
  return key
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

export function recommendationContextValue(key: string, value: unknown): string {
  if (key === "home_size" && typeof value === "string") {
    const label = homeSizeLabel(value);
    if (label !== null) {
      return label;
    }
  }

  if (value === "yes") {
    return "Yes";
  }

  if (value === "no") {
    return "No";
  }

  if (value === "unsure") {
    return "Not sure";
  }

  if (value === null || value === undefined || value === "") {
    return "—";
  }

  return String(value).replaceAll("_", " ");
}

export type RequestView = "active" | "closed" | "all";

export type RecommendationTriageView =
  | "all"
  | "guided"
  | "human_review"
  | "lab_testing";
