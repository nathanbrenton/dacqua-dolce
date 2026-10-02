import type { CommercialAddress } from "./commercial";

export type SalesArea = {
  enforcement_enabled: boolean;
  country_code: string;
  region_codes: string[];
  label: string;
};

export async function getSalesArea(): Promise<SalesArea> {
  const response = await fetch(
    "/api/catalog/sales-area",
    {
      credentials: "include",
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Sales-area request failed: ${response.status}`,
    );
  }

  return response.json() as Promise<SalesArea>;
}

export function salesAreaAllowsAddress(
  salesArea: SalesArea,
  address: CommercialAddress | null,
): boolean {
  if (!salesArea.enforcement_enabled) {
    return true;
  }

  if (address === null) {
    return false;
  }

  return (
    address.country_code.trim().toUpperCase()
      === salesArea.country_code
    && salesArea.region_codes.includes(
      address.region_code.trim().toUpperCase(),
    )
  );
}
