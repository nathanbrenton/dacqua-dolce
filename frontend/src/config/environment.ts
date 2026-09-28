export type AppEnvironment =
  | "development"
  | "test"
  | "production";

function resolveEnvironment(
  rawValue: string | undefined,
): AppEnvironment {
  const normalized = (
    rawValue ?? "development"
  ).trim().toLowerCase();

  if (
    normalized === "development"
    || normalized === "test"
    || normalized === "production"
  ) {
    return normalized;
  }

  throw new Error(
    `Unsupported VITE_APP_ENVIRONMENT: ${rawValue}`,
  );
}

export const APP_ENVIRONMENT = resolveEnvironment(
  import.meta.env.VITE_APP_ENVIRONMENT,
);

export const DEVELOPER_MODE =
  import.meta.env.VITE_DEVELOPER_MODE === "true";

export const IS_PRODUCTION =
  APP_ENVIRONMENT === "production";

if (IS_PRODUCTION && DEVELOPER_MODE) {
  throw new Error(
    "Developer mode must be disabled in production builds.",
  );
}
