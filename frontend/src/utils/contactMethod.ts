/** How a customer prefers to hear from us. Mirrors backend app/core/contact_method.py. */

export const CONTACT_METHOD_OPTIONS = [
  { value: "email", label: "Email" },
  { value: "call", label: "Phone call" },
  { value: "text", label: "Text message" },
] as const;

export type ContactMethod = (typeof CONTACT_METHOD_OPTIONS)[number]["value"];

export const DEFAULT_CONTACT_METHOD: ContactMethod = "email";

export const PHONE_REQUIRED_MESSAGE =
  "Add a phone number so we can call or text you.";

export function isContactMethod(value: unknown): value is ContactMethod {
  return CONTACT_METHOD_OPTIONS.some((option) => option.value === value);
}

export function contactMethodLabel(value: unknown): string | null {
  return CONTACT_METHOD_OPTIONS.find((option) => option.value === value)?.label ?? null;
}

/** Calls and texts need a phone number; email never does. */
export function contactMethodNeedsPhone(method: ContactMethod): boolean {
  return method === "call" || method === "text";
}

/** Short note shown under the dropdown for the chosen method. */
export function contactMethodHint(method: ContactMethod): string {
  switch (method) {
    case "call":
      return "We'll call the number above.";
    case "text":
      return "We'll text the number above about your request. Message and data rates may apply.";
    default:
      return "We'll reply to the email address above.";
  }
}

/** How the quote confirmation says we'll follow up: "…will review it and {phrase}." */
export function contactMethodFollowUp(method: ContactMethod): string {
  switch (method) {
    case "call":
      return "call you";
    case "text":
      return "text you";
    default:
      return "reply by email";
  }
}
