// Catalog workspace constants, labels and per-product draft shapes, shared by
// the product card sections in this folder (and by product labels elsewhere
// in Operations).

import type { OperationsProduct } from "../../../api/operations";
import { minorToDollars, parseDollarsToMinor } from "../operationsMoney";
import { localDateTimeValue } from "../operationsShared";

export const PRODUCT_LIFECYCLE_LABELS: Record<string, string> = {
  active: "Active",
  soon_discontinued: "Soon to be discontinued",
  discontinued: "Discontinued",
};

export const PRODUCT_LIFECYCLE_STATUSES = [
  "active",
  "soon_discontinued",
  "discontinued",
] as const;

export const PRICING_MODES = [
  "PUBLIC",
  "MAP_LIMITED",
  "CART_ONLY",
  "PRIVATE_QUOTE",
  "LOGIN_REQUIRED",
  "NO_ONLINE_PRICE",
  "NO_ONLINE_SALE",
] as const;

export const AMOUNT_REQUIRED = new Set<string>([
  "PUBLIC",
  "MAP_LIMITED",
  "CART_ONLY",
  "LOGIN_REQUIRED",
]);

export const PROMOTION_SUPPORTED_MODES = new Set<string>([
  "PUBLIC",
  "CART_ONLY",
  "LOGIN_REQUIRED",
]);

export const INVENTORY_STATUSES = [
  "in_stock",
  "low_stock",
  "backordered",
  "unavailable",
  "not_tracked",
] as const;

export const INVENTORY_SOURCE_KINDS = [
  "unspecified",
  "operator_entry",
  "supplier_report",
  "manufacturer_report",
  "internal_stock",
] as const;

export const PRICING_MODE_LABELS: Record<string, string> = {
  PUBLIC: "Public price",
  MAP_LIMITED: "MAP-limited",
  CART_ONLY: "Cart only",
  PRIVATE_QUOTE: "Private quote",
  LOGIN_REQUIRED: "Login required",
  NO_ONLINE_PRICE: "No online price",
  NO_ONLINE_SALE: "No online sale",
};

export const INVENTORY_STATUS_LABELS: Record<string, string> = {
  in_stock: "In stock",
  low_stock: "Low stock",
  backordered: "Backordered",
  unavailable: "Unavailable",
  not_tracked: "Not tracked",
};

export const INVENTORY_SOURCE_LABELS: Record<string, string> = {
  unspecified: "Not recorded",
  operator_entry: "Operator entry",
  supplier_report: "Supplier report",
  manufacturer_report: "Manufacturer report",
  internal_stock: "Internal stock",
};

export type PricingDraft = {
  mode: string;
  amount: string;
  currency: string;
};

export type TaxClassificationDraft = {
  taxCode: string;
  sourceReference: string;
};

export type PromotionDraft = {
  amount: string;
  startLocal: string;
  endLocal: string;
};

export type InventoryDraft = {
  status: string;
  quantityOnHand: string;
  expectedAvailableOn: string;
  estimatedLeadTime: string;
  sourceKind: OperationsProduct["inventory"]["source_kind"];
  sourceReference: string;
};

export type AvailabilityPolicyDraft = {
  lifecycleStatus: OperationsProduct["lifecycle_status"];
  publicRetireLocal: string;
  allowInquiryWhenUnavailable: boolean;
  allowFormalQuoteWhenUnavailable: boolean;
};


export function dollarsToMinor(value: string): number | null {
  return parseDollarsToMinor(value);
}

export function pricingDraftFrom(product: OperationsProduct): PricingDraft {
  return {
    mode: product.standard_pricing.mode,
    amount: minorToDollars(product.standard_pricing.amount_minor),
    currency: product.standard_pricing.currency ?? "USD",
  };
}

export const EMPTY_PROMOTION_DRAFT: PromotionDraft = {
  amount: "",
  startLocal: "",
  endLocal: "",
};

export function taxClassificationDraftFrom(
  product: OperationsProduct,
): TaxClassificationDraft {
  return {
    taxCode: product.tax_classification?.tax_code ?? "",
    sourceReference: product.tax_classification?.source_reference ?? "",
  };
}

export function inventoryDraftFrom(product: OperationsProduct): InventoryDraft {
  return {
    status: product.inventory.status,
    quantityOnHand: String(product.inventory.quantity_on_hand),
    expectedAvailableOn: product.inventory.expected_available_on ?? "",
    estimatedLeadTime: product.inventory.estimated_lead_time ?? "",
    sourceKind: product.inventory.source_kind,
    sourceReference: product.inventory.source_reference ?? "",
  };
}

export function availabilityPolicyDraftFrom(
  product: OperationsProduct,
): AvailabilityPolicyDraft {
  return {
    lifecycleStatus: product.lifecycle_status,
    publicRetireLocal: product.public_retire_at === null
      ? ""
      : localDateTimeValue(new Date(product.public_retire_at)),
    allowInquiryWhenUnavailable: product.allow_inquiry_when_unavailable,
    allowFormalQuoteWhenUnavailable: product.allow_formal_quote_when_unavailable,
  };
}
