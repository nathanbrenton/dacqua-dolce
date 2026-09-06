export type AuthenticationStatus = {
  authenticated: boolean;
  email: string | null;
  roles: string[];
};

type AuthenticationPayload = {
  email: string;
  password: string;
};

type ErrorPayload = {
  detail?: string;
};

async function readError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ErrorPayload;

    if (typeof payload.detail === "string") {
      return payload.detail;
    }
  } catch {
    // Fall through to a generic message.
  }

  return `Request failed with status ${response.status}.`;
}

export async function getCsrfToken(): Promise<string> {
  const response = await fetch("/api/auth/csrf", {
    credentials: "include",
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const payload = (await response.json()) as {
    csrf_token: string;
  };

  return payload.csrf_token;
}

async function submitAuthentication(
  endpoint: "/api/auth/login" | "/api/auth/register",
  payload: AuthenticationPayload,
): Promise<AuthenticationStatus> {
  const csrfToken = await getCsrfToken();

  const response = await fetch(endpoint, {
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

  return response.json() as Promise<AuthenticationStatus>;
}

export function loginAccount(
  payload: AuthenticationPayload,
): Promise<AuthenticationStatus> {
  return submitAuthentication("/api/auth/login", payload);
}

export function registerAccount(
  payload: AuthenticationPayload,
): Promise<AuthenticationStatus> {
  return submitAuthentication("/api/auth/register", payload);
}

export async function getCurrentAccount(): Promise<AuthenticationStatus | null> {
  const response = await fetch("/api/auth/me", {
    credentials: "include",
    cache: "no-store",
  });

  if (response.status === 401) {
    return null;
  }

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<AuthenticationStatus>;
}

export async function logoutAccount(): Promise<void> {
  const csrfToken = await getCsrfToken();

  const response = await fetch("/api/auth/logout", {
    method: "POST",
    credentials: "include",
    cache: "no-store",
    headers: {
      "X-CSRF-Token": csrfToken,
    },
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }
}
