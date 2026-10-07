type ApiValidationIssue = {
  loc?: unknown;
  msg?: unknown;
};

type ApiErrorPayload = {
  detail?: unknown;
};

function fieldLabel(
  location: unknown,
): string | null {
  if (!Array.isArray(location)) {
    return null;
  }

  const candidate = [...location]
    .reverse()
    .find(
      (part) =>
        typeof part === "string"
        && part !== "body"
        && part !== "query"
        && part !== "path",
    );

  if (typeof candidate !== "string") {
    return null;
  }

  return candidate
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function cleanValidationMessage(
  message: string,
): string {
  return message
    .replace(/^Value error,\s*/i, "")
    .trim();
}

function validationIssueMessage(
  issue: ApiValidationIssue,
): string | null {
  if (typeof issue.msg !== "string") {
    return null;
  }

  const message = cleanValidationMessage(issue.msg);

  if (message.length === 0) {
    return null;
  }

  const label = fieldLabel(issue.loc);

  return label === null
    ? message
    : `${label}: ${message}`;
}

export async function readApiError(
  response: Response,
  fallbackLabel: string,
): Promise<string> {
  try {
    const payload =
      (await response.json()) as ApiErrorPayload;

    if (
      typeof payload.detail === "string"
      && payload.detail.trim().length > 0
    ) {
      return payload.detail.trim();
    }

    if (Array.isArray(payload.detail)) {
      const messages = payload.detail
        .map((issue) =>
          validationIssueMessage(
            issue as ApiValidationIssue,
          ),
        )
        .filter(
          (message): message is string =>
            message !== null,
        );

      if (messages.length > 0) {
        return messages.join(" ");
      }
    }
  } catch {
    // Fall through to the stable status fallback.
  }

  return `${fallbackLabel}: ${response.status}`;
}
