export type CommercialChargeKind =
  | "shipping"
  | "tax"
  | "installation"
  | "discount"
  | "other_charge"
  | "other_credit";

export type CommercialCharge = {
  kind: CommercialChargeKind;
  label: string;
  amount_minor: number;
};

export type CommercialAddress = {
  recipient_name: string;
  line1: string;
  line2: string | null;
  city: string;
  region_code: string;
  postal_code: string;
  country_code: string;
  phone: string | null;
};
