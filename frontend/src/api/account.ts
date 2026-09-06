import { getCsrfToken } from "./authentication";

export type CustomerAddress = {
  id: string;
  label: string;
  line1: string;
  line2: string | null;
  city: string;
  region_code: string;
  postal_code: string;
  country_code: string;
  is_default_shipping: boolean;
  is_default_billing: boolean;
};

export type CustomerProfile = {
  email: string;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  addresses: CustomerAddress[];
};

export type CustomerProfileUpdate = {
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
};

export type AddressCreate = Omit<
  CustomerAddress,
  "id"
>;

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

  return `Account request failed: ${response.status}`;
}

export async function getProfile(): Promise<CustomerProfile> {
  const response = await fetch(
    "/api/account/profile",
    {
      credentials: "include",
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      await readError(response),
    );
  }

  return response.json() as Promise<CustomerProfile>;
}

export async function updateProfile(
  payload: CustomerProfileUpdate,
): Promise<CustomerProfile> {
  const csrfToken = await getCsrfToken();

  const response = await fetch(
    "/api/account/profile",
    {
      method: "PUT",
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

  return response.json() as Promise<CustomerProfile>;
}

export async function createAddress(
  payload: AddressCreate,
): Promise<CustomerAddress> {
  const csrfToken = await getCsrfToken();

  const response = await fetch(
    "/api/account/addresses",
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

  return response.json() as Promise<CustomerAddress>;
}

export async function deleteAddress(
  id: string,
): Promise<void> {
  const csrfToken = await getCsrfToken();

  const response = await fetch(
    `/api/account/addresses/${encodeURIComponent(id)}`,
    {
      method: "DELETE",
      credentials: "include",
      cache: "no-store",
      headers: {
        "X-CSRF-Token": csrfToken,
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      await readError(response),
    );
  }
}
