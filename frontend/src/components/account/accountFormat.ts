// Display helpers shared by the customer account sections.

import { type CustomerFormalQuote } from "../../api/account";
import { CommercialAddress } from "../../api/commercial";

export function money(
  amountMinor: number,
  currency: string,
): string {
  return new Intl.NumberFormat(
    undefined,
    {
      style: "currency",
      currency,
    },
  ).format(amountMinor / 100);
}

export function formalQuoteExpired(quote: CustomerFormalQuote): boolean {
  return quote.expires_at !== null
    && new Date(quote.expires_at).getTime() <= Date.now();
}

export function commercialAddressLines(address: CommercialAddress): string[] {
  return [
    address.recipient_name,
    address.line1,
    address.line2,
    `${address.city}, ${address.region_code} ${address.postal_code}`,
    address.country_code,
    address.phone,
  ].filter((value): value is string => value !== null && value !== "");
}

const ORDER_STAGE_LABELS: Record<string, string> = {
  received: "Received",
  processing: "Processing",
  supplier_confirmed: "Supplier Confirmed",
  awaiting_shipment: "Awaiting Shipment",
  shipped: "Shipped",
  completed: "Completed",
  cancelled: "Cancelled",
  refunded: "Refunded",
};

export function orderStageLabel(value: string): string {
  return ORDER_STAGE_LABELS[value] ?? value.replaceAll("_", " ");
}
