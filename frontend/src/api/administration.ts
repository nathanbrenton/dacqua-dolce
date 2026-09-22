import {
  getCsrfToken,
} from "./authentication";

export type AdministrationAccount = {
  id: string;
  email: string;
  status: string;
  roles: string[];
  email_verified: boolean;
  mfa_required: boolean;
  mfa_enrolled: boolean;
  created_at: string;
  last_login_at: string | null;
};

export type WebManagedRole =
  | "employee"
  | "manager"
  | "administrator";

type ErrorPayload = {
  detail?: string;
};

async function readError(
  response: Response,
): Promise<string> {
  try {
    const payload =
      (await response.json()) as ErrorPayload;

    if (
      typeof payload.detail
      === "string"
    ) {
      return payload.detail;
    }
  } catch {
    // Fall through to a generic message.
  }

  return (
    "Administration request failed: "
    + response.status
  );
}

export async function getAdministrationAccounts(): Promise<
  AdministrationAccount[]
> {
  const response = await fetch(
    "/api/administration/accounts",
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

  return response.json() as Promise<
    AdministrationAccount[]
  >;
}

export async function updateAdministrationRoles(
  userId: string,
  roles: WebManagedRole[],
): Promise<AdministrationAccount> {
  const csrfToken = await getCsrfToken();

  const response = await fetch(
    `/api/administration/accounts/${encodeURIComponent(userId)}/roles`,
    {
      method: "PUT",
      credentials: "include",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({ roles }),
    },
  );

  if (!response.ok) {
    throw new Error(
      await readError(response),
    );
  }

  return response.json() as Promise<
    AdministrationAccount
  >;
}
